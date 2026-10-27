"""V2 reading metrics: truth is explicit, bounded, and isolated from V1."""
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from db.learning_models import V2AudioRubric
from v2_audio_rubric import ReadingRubricV2, save_v2_reading_rubric


@pytest.mark.parametrize("payload", [
    {"target_units": 0},
    {"target_units": -1},
    {"target_units": 4, "deletions": -1},
    {"target_units": 3, "deletions": 2, "substitutions": 2},
    {"target_units": 1001},
    {"target_units": 3, "insertions": -1},
])
def test_invalid_counts_rejected_before_grade(payload):
    with pytest.raises(ValidationError):
        ReadingRubricV2.model_validate(payload)


def test_numeric_score_never_decides_binary_mastery():
    rubric = ReadingRubricV2(target_units=6, deletions=1, substitutions=1, insertions=1)
    assert rubric.observed_score() == Decimal("0.5")
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    audio = SimpleNamespace(id=81, lesson_response_id=40, assessment_response_id=None)
    save_v2_reading_rubric(db, audio=audio, reviewer_id=7, is_correct=False, rubric=rubric)
    saved = db.add.call_args.args[0]
    assert isinstance(saved, V2AudioRubric)
    assert saved.audio_submission_id == 81
    assert saved.is_correct is False
    assert saved.rubric_score == Decimal("0.5")
    assert saved.policy_version.startswith("himma-v2-reading-rubric/")
    assert saved.target_units == 6
    # The same 100%-accuracy observation may still be a human "not met"
    # judgment (e.g. no reliable fluency): never score >0 => True.
    db.reset_mock()
    db.query.return_value.filter.return_value.first.return_value = None
    save_v2_reading_rubric(
        db, audio=audio, reviewer_id=7, is_correct=False,
        rubric=ReadingRubricV2(target_units=6),
    )
    perfect = db.add.call_args.args[0]
    assert perfect.rubric_score == Decimal("1")
    assert perfect.is_correct is False


def test_duplicate_audio_rubric_does_not_create_second_ledger_row():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = (55,)
    audio = SimpleNamespace(id=81, lesson_response_id=None, assessment_response_id=41)
    with pytest.raises(HTTPException) as error:
        save_v2_reading_rubric(
            db, audio=audio, reviewer_id=7, is_correct=True,
            rubric=ReadingRubricV2(target_units=3),
        )
    assert error.value.status_code == 409
    db.add.assert_not_called()


def test_reject_legacy_audio_ownership():
    db = MagicMock()
    audio = SimpleNamespace(id=81, lesson_response_id=None, assessment_response_id=None)
    with pytest.raises(HTTPException) as error:
        save_v2_reading_rubric(
            db, audio=audio, reviewer_id=7, is_correct=True,
            rubric=ReadingRubricV2(target_units=3),
        )
    assert error.value.status_code == 409
    db.add.assert_not_called()
