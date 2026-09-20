"""Parity and separation gates for student content and admin content review.

The admin page must expose the approved academic truth (including answers), while
student payloads must continue to hide answer metadata. Both surfaces read the
same published PostgreSQL rows and preview must never create progress.
"""
from __future__ import annotations

from types import SimpleNamespace

import content_preview
import learning_experience
import seed_all
from content_runtime import canonical_id
from content_student_view import activity_student_content, assessment_student_payload
from db.database import SessionLocal
from db.models import AssessmentSession, Attempt, AttemptResponse, AudioSubmission, ContentItem, Student


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


def test_admin_assessment_review_exposes_truth_while_student_payload_hides_it():
    _seed()
    db = SessionLocal()
    try:
        item = _by_canonical(db, "PRE-Q17")
        step = sorted(item.steps, key=lambda value: value.order_index)[0]

        student_payload = assessment_student_payload(item, step)
        review = content_preview.get_content_preview("PRE-Q17", db=db, _=None)

        assert review["mode"] == "read_only"
        assert review["purpose"] == "admin_content_review"
        assert review["writes_progress"] is False
        assert review["item"]["canonical_id"] == "PRE-Q17"
        assert len(review["rounds"]) == 1

        reviewed_round = review["rounds"][0]
        assert reviewed_round["question_text"] == student_payload["presentation"]["question_text"]
        assert {option["text"] for option in reviewed_round["options"]} == {
            option["text"] for option in student_payload["steps"][0]["options"]
        }
        assert len([option for option in reviewed_round["options"] if option["is_correct"]]) == 1
        assert reviewed_round["answer"]["kind"] == "correct_options"
        assert reviewed_round["answer"]["values"]
        assert reviewed_round["answer"]["option_ids"]

        image_assets = [
            asset for asset in reviewed_round["assets"]
            if asset.get("asset_type") == "image" and asset.get("option_id") is not None
        ]
        assert len(image_assets) == 4
        _assert_no_answer_metadata(student_payload)
    finally:
        db.close()


def test_admin_learning_review_lists_all_rounds_and_recording_target():
    _seed()
    db = SessionLocal()
    try:
        review = content_preview.get_content_preview("L2-REIN-07", db=db, _=None)
        assert review["item"]["interaction_type"] == "read_aloud"
        assert len(review["rounds"]) == 5
        assert [round_data["answer"]["kind"] for round_data in review["rounds"]] == ["recording_target"] * 5
        assert [round_data["answer"]["values"][0] for round_data in review["rounds"]] == [
            "كَتَبَ", "لَعِبَ", "رَسَمَ", "فَتَحَ", "جَلَسَ"
        ]
        assert all(round_data["options"] == [] for round_data in review["rounds"])
    finally:
        db.close()


def test_admin_order_review_exposes_canonical_correct_sequence():
    _seed()
    db = SessionLocal()
    try:
        review = content_preview.get_content_preview("L1-CORE-10", db=db, _=None)
        assert review["item"]["interaction_type"] in {"sequence", "memory_sequence", "path_sequence", "build_word"}
        for round_data in review["rounds"]:
            assert round_data["answer"]["kind"] == "ordered_sequence"
            assert round_data["answer"]["values"] == [option["text"] for option in round_data["options"]]
    finally:
        db.close()


def test_admin_content_review_creates_no_student_progress_rows():
    _seed()
    db = SessionLocal()
    try:
        before = {
            "sessions": db.query(AssessmentSession).count(),
            "attempts": db.query(Attempt).count(),
            "responses": db.query(AttemptResponse).count(),
            "audio": db.query(AudioSubmission).count(),
        }
        content_preview.list_content_preview(db=db, _=None)
        content_preview.get_content_preview("L1-CORE-09", db=db, _=None)
        after = {
            "sessions": db.query(AssessmentSession).count(),
            "attempts": db.query(Attempt).count(),
            "responses": db.query(AttemptResponse).count(),
            "audio": db.query(AudioSubmission).count(),
        }
        assert after == before
    finally:
        db.close()


def test_live_learning_student_contract_stays_answer_safe(monkeypatch):
    _seed()
    db = SessionLocal()
    try:
        item = _by_canonical(db, "L1-CORE-09")
        step = sorted(item.steps, key=lambda value: value.order_index)[0]
        expected = activity_student_content(item, step)

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
        assert live["round"]["question_text"] == expected["step"]["question_text"]
        assert live["step"]["options"] == expected["step"]["options"]
        assert live["step"]["assets"] == expected["step"]["assets"]
        _assert_no_answer_metadata(live)
    finally:
        db.close()


def test_admin_core_review_exposes_approved_reinforcement_branch_and_searchable_question_text():
    _seed()
    db = SessionLocal()
    try:
        review = content_preview.get_content_preview("L1-CORE-09", db=db, _=None)
        assert review["item"]["reinforcement_candidates"] == ["L1-REIN-11"]

        index = content_preview.list_content_preview(db=db, _=None)
        summary = next(item for item in index["items"] if item["canonical_id"] == "L1-CORE-09")
        assert summary["reinforcement_candidates"] == ["L1-REIN-11"]
        assert review["rounds"][0]["question_text"] in summary["search_text"]
    finally:
        db.close()
