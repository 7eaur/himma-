"""Regression coverage for separating learner navigation from audio-review evidence."""
from __future__ import annotations

from activity_runtime import (
    _next_unattempted_core_item,
    effective_step_state,
    navigation_target,
)
from db.database import SessionLocal
from db.models import (
    AssessmentSession,
    Attempt,
    AttemptResponse,
    AudioSubmission,
    ContentItem,
    ContentOption,
    ContentStep,
    Skill,
    Student,
)


def _build_pending_audio_case():
    db = SessionLocal()
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    skill = Skill(
        skill_key="audio-navigation-test",
        name="اختبار التنقل الصوتي",
        description="fixture",
        level_id=1,
        canonical_skill_id="audio_navigation_test",
    )
    db.add(skill)
    db.flush()

    reading = ContentItem(
        stable_key="test:audio-navigation:reading",
        kind="core_activity",
        level_id=1,
        skill_id=skill.id,
        interaction_type="read_aloud",
        order_index=1,
        version="test",
        status="approved",
        checksum="a" * 64,
        template_data={"canonical_interaction_type": "read_aloud"},
    )
    choice = ContentItem(
        stable_key="test:audio-navigation:choice",
        kind="core_activity",
        level_id=1,
        skill_id=skill.id,
        interaction_type="choose_one",
        order_index=2,
        version="test",
        status="approved",
        checksum="b" * 64,
        template_data={"canonical_interaction_type": "choose_one"},
    )
    db.add_all([reading, choice])
    db.flush()

    reading_step = ContentStep(
        item_id=reading.id,
        order_index=1,
        prompt_text="اقرأ الكلمة.",
        expected_reading_text="كتاب",
    )
    choice_step = ContentStep(
        item_id=choice.id,
        order_index=1,
        prompt_text="اختر الإجابة.",
    )
    db.add_all([reading_step, choice_step])
    db.flush()
    db.add_all([
        ContentOption(step_id=choice_step.id, text="أ", is_correct=True, order_index=1),
        ContentOption(step_id=choice_step.id, text="ب", is_correct=False, order_index=2),
    ])

    session = AssessmentSession(
        student_id=student.id,
        session_type="core",
        status="in_progress",
        assigned_level=1,
    )
    db.add(session)
    db.flush()

    attempt = Attempt(session_id=session.id, item_id=reading.id, status="in_progress")
    db.add(attempt)
    db.flush()
    response = AttemptResponse(
        attempt_id=attempt.id,
        step_id=reading_step.id,
        selected_option_id=None,
        is_correct=None,
        elapsed_seconds=3,
    )
    db.add(response)
    db.flush()
    audio = AudioSubmission(
        response_id=response.id,
        storage_key=f"audio/{student.id}/pending.webm",
        file_size=100,
        mime_type="audio/webm",
        duration_seconds=3,
        status="uploaded",
    )
    db.add(audio)
    db.commit()
    db.refresh(reading_step)
    db.refresh(attempt)
    db.refresh(session)
    return db, student, session, attempt, reading_step, response, audio, choice


def test_pending_audio_is_academically_open_but_not_a_navigation_blocker(monkeypatch):
    db, student, session, attempt, step, _, _, choice = _build_pending_audio_case()
    try:
        state = effective_step_state(db, attempt, step)
        assert state["done"] is False
        assert state["last_correct"] is None
        assert state["awaiting_audio_review"] is True

        current_attempt, _, current_step, pending_count, _ = navigation_target(
            db,
            session.id,
            finalize_completed=False,
        )
        assert current_attempt is None
        assert current_step is None
        assert pending_count == 1
        assert attempt.status == "in_progress"

        monkeypatch.setattr("activity_runtime._preferred_core_skill_id", lambda *args, **kwargs: None)
        next_item = _next_unattempted_core_item(
            db,
            student_id=student.id,
            session_id=session.id,
            level_id=1,
        )
        assert next_item is not None
        assert next_item.id == choice.id
    finally:
        db.close()


def test_pending_item_is_reserved_and_cannot_be_selected_again(monkeypatch):
    db, student, session, attempt, _, _, _, choice = _build_pending_audio_case()
    try:
        monkeypatch.setattr("activity_runtime._preferred_core_skill_id", lambda *args, **kwargs: None)
        next_item = _next_unattempted_core_item(
            db,
            student_id=student.id,
            session_id=session.id,
            level_id=1,
        )
        assert next_item is not None
        assert next_item.id == choice.id
        assert next_item.id != attempt.item_id
    finally:
        db.close()


def test_rerecord_required_resurfaces_the_original_step():
    db, _, session, attempt, step, _, audio, _ = _build_pending_audio_case()
    try:
        audio.status = "rerecord_required"
        db.commit()

        current_attempt, current_item, current_step, pending_count, _ = navigation_target(
            db,
            session.id,
            finalize_completed=False,
        )
        assert current_attempt is not None and current_attempt.id == attempt.id
        assert current_item is not None and current_item.id == attempt.item_id
        assert current_step is not None and current_step.id == step.id
        assert pending_count == 0
        state = effective_step_state(db, attempt, step)
        assert state["done"] is False
        assert state["awaiting_audio_review"] is False
    finally:
        db.close()


def test_only_graded_audio_can_finalize_reading_attempt():
    db, _, session, attempt, step, response, audio, _ = _build_pending_audio_case()
    try:
        # Pending review is never completion evidence.
        _, _, _, pending_count, finalized = navigation_target(
            db,
            session.id,
            finalize_completed=True,
        )
        assert pending_count == 1
        assert finalized is False
        assert attempt.status == "in_progress"

        # Supervisor result becomes the academic truth.
        response.is_correct = True
        audio.status = "graded"
        db.commit()
        _, _, _, pending_count, finalized = navigation_target(
            db,
            session.id,
            finalize_completed=True,
        )
        assert pending_count == 0
        assert finalized is True
        db.flush()
        db.refresh(attempt)
        assert attempt.status == "completed"
        assert effective_step_state(db, attempt, step)["done"] is True
    finally:
        db.close()
