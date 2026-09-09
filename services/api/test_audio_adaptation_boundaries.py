"""Regression tests for unresolved/graded audio at adaptive journey boundaries."""

from datetime import datetime, timezone
from types import SimpleNamespace

import adaptation_runtime
import seed_all
from adaptation import _attempt_signal
from db.adaptation_models import AdaptationDecision
from db.database import SessionLocal
from db.models import (
    AssessmentSession,
    Attempt,
    AttemptResponse,
    AudioSubmission,
    ContentItem,
    ContentStep,
    Skill,
    Student,
)


def _core_session(db, *, level: int = 1):
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    student.current_level = level
    session = AssessmentSession(
        student_id=student.id,
        session_type="core",
        status="in_progress",
        assigned_level=level,
    )
    db.add(session)
    db.flush()
    return student, session


def _decision(
    db,
    *,
    student: Student,
    action: str,
    previous_level: int,
    new_level: int,
    snapshot_key: str,
    recommended_item_id: int | None = None,
):
    decision = AdaptationDecision(
        student_id=student.id,
        decision_source="automatic",
        action=action,
        mastery_score=90,
        previous_level=previous_level,
        new_level=new_level,
        recommended_item_id=recommended_item_id,
        valid_attempt_count=3,
        consecutive_low_count=0,
        snapshot_key=snapshot_key,
        explanation={"reason": "audio-boundary-regression"},
    )
    db.add(decision)
    db.flush()
    return decision


def _payload(decision: AdaptationDecision) -> dict:
    return {
        "ready": True,
        "decision_id": decision.id,
        "action": decision.action,
        "previous_level": decision.previous_level,
        "new_level": decision.new_level,
    }


def test_unresolved_audio_does_not_suppress_same_level_support(monkeypatch):
    seed_all.run_seed_all()
    db = SessionLocal()
    try:
        student, session = _core_session(db, level=1)
        reinforcement = (
            db.query(ContentItem)
            .filter(
                ContentItem.kind == "reinforcement_activity",
                ContentItem.level_id == 1,
                ContentItem.status == "approved",
            )
            .order_by(ContentItem.order_index, ContentItem.id)
            .first()
        )
        assert reinforcement is not None
        decision = _decision(
            db,
            student=student,
            action="support",
            previous_level=1,
            new_level=1,
            snapshot_key="audio-boundary:support",
            recommended_item_id=reinforcement.id,
        )
        db.commit()

        monkeypatch.setattr(adaptation_runtime, "evaluate_student", lambda *args, **kwargs: _payload(decision))

        def fail_if_audio_boundary_is_checked(*args, **kwargs):
            raise AssertionError("same-level support must not consult the irreversible audio boundary gate")

        monkeypatch.setattr(adaptation_runtime, "session_audio_review_summary", fail_if_audio_boundary_is_checked)

        result = adaptation_runtime.prepare_next_for_student(db, student, session)
        assert result["decision"]["action"] == "support"
        assert result["recommended_attempt_id"] is not None
        assert result["level_transitioned"] is False
        assert result["session_id"] == session.id
        assert student.current_level == 1
    finally:
        db.close()


def test_unresolved_audio_holds_promotion_then_resolution_allows_it(monkeypatch):
    db = SessionLocal()
    try:
        student, session = _core_session(db, level=1)
        decision = _decision(
            db,
            student=student,
            action="promote",
            previous_level=1,
            new_level=2,
            snapshot_key="audio-boundary:promote",
        )
        db.commit()

        monkeypatch.setattr(adaptation_runtime, "evaluate_student", lambda *args, **kwargs: _payload(decision))
        unresolved = SimpleNamespace(
            has_unresolved=True,
            pending_count=1,
            rerecord_required_count=0,
        )
        monkeypatch.setattr(adaptation_runtime, "session_audio_review_summary", lambda *args, **kwargs: unresolved)

        held = adaptation_runtime.prepare_next_for_student(db, student, session)
        assert held["decision"]["action"] == "hold"
        assert held["decision"]["reason"] == "unresolved_audio_evidence"
        assert held["level_transitioned"] is False
        assert student.current_level == 1
        assert session.status == "in_progress"
        assert db.query(AssessmentSession).filter(
            AssessmentSession.student_id == student.id,
            AssessmentSession.session_type == "core",
            AssessmentSession.assigned_level == 2,
        ).count() == 0

        resolved = SimpleNamespace(
            has_unresolved=False,
            pending_count=0,
            rerecord_required_count=0,
        )
        monkeypatch.setattr(adaptation_runtime, "session_audio_review_summary", lambda *args, **kwargs: resolved)

        promoted = adaptation_runtime.prepare_next_for_student(db, student, session)
        assert promoted["level_transitioned"] is True
        assert promoted["transition_direction"] == "promotion"
        assert promoted["level_id"] == 2
        assert student.current_level == 2
        assert session.status == "completed"
        next_session = db.query(AssessmentSession).filter(
            AssessmentSession.id == promoted["session_id"],
        ).one()
        assert next_session.assigned_level == 2
        assert next_session.status == "in_progress"
    finally:
        db.close()


def test_only_graded_audio_enters_adaptation_evidence():
    db = SessionLocal()
    try:
        student, session = _core_session(db, level=1)
        skill = Skill(
            skill_key="audio-boundary-test-skill",
            name="مهارة صوتية اختبارية",
            level_id=1,
            canonical_skill_id="TEST-AUDIO-BOUNDARY",
        )
        db.add(skill)
        db.flush()
        item = ContentItem(
            stable_key="TEST-AUDIO-BOUNDARY-ITEM",
            kind="core_activity",
            level_id=1,
            skill_id=skill.id,
            interaction_type="read_aloud",
            order_index=99,
            version="test",
            status="approved",
            checksum="0" * 64,
            template_data={},
        )
        db.add(item)
        db.flush()
        step = ContentStep(
            item_id=item.id,
            order_index=1,
            prompt_text="اقرأ",
            expected_reading_text="مَ",
        )
        db.add(step)
        db.flush()
        attempt = Attempt(
            session_id=session.id,
            item_id=item.id,
            status="completed",
            completed_at=datetime.now(timezone.utc),
        )
        db.add(attempt)
        db.flush()
        response = AttemptResponse(
            attempt_id=attempt.id,
            step_id=step.id,
            is_correct=True,
        )
        db.add(response)
        db.flush()
        submission = AudioSubmission(
            response_id=response.id,
            storage_key=f"audio/{student.id}/boundary.webm",
            file_size=128,
            mime_type="audio/webm",
            duration_seconds=1.0,
            status="uploaded",
        )
        db.add(submission)
        db.commit()

        assert _attempt_signal(db, attempt, item) is None

        submission.status = "graded"
        db.commit()
        signal = _attempt_signal(db, attempt, item)
        assert signal is not None
        assert signal.attempt_id == attempt.id
        assert signal.skill_id == skill.id
        assert signal.score == 100.0
    finally:
        db.close()
