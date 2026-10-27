"""Historical IDs survive publication; only active options accept new answers."""
import pytest
from fastapi import HTTPException

import seed
from assessment import _validate_option_ids
from content_option_lifecycle import set_exact_current_options, visible_key
from db.database import SessionLocal
from db.models import ContentItem, ContentOption


def test_publication_preserves_old_rows_and_is_idempotent():
    seed.run_seed()
    with SessionLocal() as db:
        item = db.query(ContentItem).filter(ContentItem.kind == "pretest_question").order_by(ContentItem.id).first()
        step = item.steps[0]
        old = [(o.id, o.text, o.is_correct, o.order_index) for o in step.options]
        set_exact_current_options(db, step, [("مَ", True), ("مِ", False)])
        active = [o.id for o in step.options]
        db.commit()
        assert len(active) == 2
        for identity, text, correct, order in old:
            row = db.get(ContentOption, identity)
            assert (row.text, row.is_correct, row.order_index) == (text, correct, order)
            assert row.is_active is False
        with pytest.raises(HTTPException):
            _validate_option_ids(step, [old[0][0]])
        assert set_exact_current_options(db, step, [("مَ", True), ("مِ", False)]) == {"created": 0, "retired": 0, "reactivated": 0}
        assert [o.id for o in step.options] == active
        result = set_exact_current_options(db, step, [("مَ", False), ("مِ", True)])
        assert result["created"] == 2
        assert db.get(ContentOption, active[0]).is_correct is True


def test_normalization_preserves_academic_forms_and_vowels():
    assert visible_key("مَ") != visible_key("مِ")
    assert visible_key("ب") != visible_key("بـ")
    assert visible_key("ب\u200f") == visible_key("ب")


def test_duplicate_rejection_and_intentional_repeated_letter_tokens():
    seed.run_seed()
    with SessionLocal() as db:
        step = db.query(ContentItem).order_by(ContentItem.id).first().steps[0]
        with pytest.raises(ValueError, match="Duplicate"):
            set_exact_current_options(db, step, [("ب", True), ("ب\u200f", False)])
        set_exact_current_options(db, step, [("ب", False), ("ا", False), ("ب", False)], allow_repeated=True)
        assert [o.text for o in step.options] == ["ب", "ا", "ب"]
        assert len({o.id for o in step.options}) == 3
