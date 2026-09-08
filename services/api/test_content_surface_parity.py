"""Parity gates for every read-only/live student content surface.

The canonical publisher owns academic data.  These tests make sure researcher
preview and live learner rendering delegate to the exact same serializers, so a
wording/media/options fix cannot appear in one surface and silently drift in the
other.
"""
from types import SimpleNamespace

import content_preview
import learning_experience
import seed_all
from content_runtime import canonical_id
from content_student_view import activity_student_content, assessment_student_payload
from db.database import SessionLocal
from db.models import AssessmentSession, ContentItem, Student


FORBIDDEN_STUDENT_KEYS = {
    "source_text",
    "is_correct",
    "correct_answer",
    "correct_option_id",
    "correct_option_ids",
    "answer_key",
    "answer_sequence",
}


def _seed() -> None:
    result = seed_all.run_seed_all()
    assert result["total_items"] == 125
    assert result["pretest_items"] == 30
    assert result["posttest_items"] == 30
    assert result["core_items"] == 30
    assert result["reinforcement_items"] == 35


def _by_canonical(db, wanted: str) -> ContentItem:
    for item in db.query(ContentItem).all():
        if canonical_id(item) == wanted:
            return item
    raise AssertionError(f"Missing canonical item {wanted}")


def _assert_no_answer_metadata(value, path: str = "payload") -> None:
    if isinstance(value, dict):
        leaked = FORBIDDEN_STUDENT_KEYS.intersection(value)
        assert not leaked, (path, sorted(leaked))
        for key, child in value.items():
            _assert_no_answer_metadata(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_no_answer_metadata(child, f"{path}[{index}]")


def test_assessment_preview_is_exact_student_serializer_and_leaks_no_answers():
    _seed()
    db = SessionLocal()
    try:
        item = _by_canonical(db, "PRE-Q17")
        step = sorted(item.steps, key=lambda value: value.order_index)[0]
        expected = assessment_student_payload(item, step)
        preview = content_preview.get_content_preview("PRE-Q17", db=db, _=None)

        assert preview["mode"] == "read_only"
        assert preview["writes_progress"] is False
        assert preview["surface"] == "assessment"
        assert preview["payload"] == expected
        assert len(expected["steps"][0]["options"]) == 4
        assert len([
            asset for asset in expected["steps"][0]["assets"]
            if asset.get("asset_type") == "image" and asset.get("option_id") is not None
        ]) == 4
        _assert_no_answer_metadata(preview)
    finally:
        db.close()


def test_learning_preview_and_live_route_share_one_static_contract(monkeypatch):
    _seed()
    db = SessionLocal()
    try:
        item = _by_canonical(db, "L1-CORE-09")
        steps = sorted(item.steps, key=lambda value: value.order_index)
        step = steps[0]
        expected = activity_student_content(item, step)

        preview = content_preview.get_content_preview("L1-CORE-09", db=db, _=None)
        assert preview["mode"] == "read_only"
        assert preview["writes_progress"] is False
        assert preview["surface"] == "learning"
        assert preview["payload"]["item"] == expected["item"]
        assert preview["payload"]["rounds"][0] == expected["step"]
        assert len(preview["payload"]["rounds"]) == 5

        student = Student(access_code="PARITY01", name="طالب المعاينة", current_level=1)
        db.add(student)
        db.flush()
        session = AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="in_progress",
            assigned_level=1,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        db.refresh(student)

        attempt = SimpleNamespace(id=987654, item_id=item.id, session_id=session.id)
        monkeypatch.setattr(
            learning_experience,
            "navigation_target",
            lambda *_args, **_kwargs: (attempt, item, step, 0, False),
        )
        monkeypatch.setattr(
            learning_experience,
            "effective_step_state",
            lambda *_args, **_kwargs: {
                "done": False,
                "attempts_used": 0,
                "audio_review_status": None,
                "awaiting_audio_review": False,
            },
        )

        live = learning_experience.current_learning_experience(
            session_id=session.id,
            db=db,
            student=student,
        )

        assert live["item_id"] == expected["item"]["id"]
        assert live["stable_key"] == expected["item"]["stable_key"]
        assert live["kind"] == expected["item"]["kind"]
        assert live["level_id"] == expected["item"]["level_id"]
        assert live["interaction_type"] == expected["item"]["interaction_type"]
        assert live["layout_hint"] == expected["item"]["layout_hint"]
        assert live["assets"] == expected["item"]["assets"]

        assert live["round"] == {
            "round_number": expected["step"]["round_number"],
            "round_total": expected["step"]["round_total"],
            "skill": expected["step"]["skill"],
            "encouragement": expected["step"]["encouragement"],
            "hint": expected["step"]["hint"],
            "question_text": expected["step"]["question_text"],
            "instruction_text": expected["step"]["instruction_text"],
            "stimulus_text": expected["step"]["stimulus_text"],
            "stimulus": expected["step"]["stimulus"],
        }
        assert live["step"] == {
            "id": expected["step"]["id"],
            "order_index": expected["step"]["order_index"],
            "expected_reading_text": expected["step"]["expected_reading_text"],
            "required_selection_count": expected["step"]["required_selection_count"],
            "options": expected["step"]["options"],
            "assets": expected["step"]["assets"],
            "media_gaps": expected["step"]["media_gaps"],
        }

        context = live["context_intro"]
        assert context is not None
        assert context["audio_asset_id"] == "INS-01"
        assert context["asset"]["asset_id"] == "INS-01"
        assert context["asset"]["asset_type"] == "audio"
        _assert_no_answer_metadata(preview)
        _assert_no_answer_metadata(live)
    finally:
        db.close()
