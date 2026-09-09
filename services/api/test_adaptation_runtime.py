"""Integration-level P06 tests for recommendation and reward persistence."""

import adaptation_runtime
from adaptation import ensure_rewards
from adaptation_runtime import prepare_next_for_student
from db.activity_models import ActivityStepResponse
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


def _item(db, *, stable_key: str, kind: str, skill_id: int, order_index: int):
    item = ContentItem(
        stable_key=stable_key,
        kind=kind,
        level_id=1,
        skill_id=skill_id,
        interaction_type="choose_one",
        order_index=order_index,
        version="test",
        status="approved",
        checksum=(stable_key * 64)[:64],
        template_data={"canonical_id": stable_key, "canonical_interaction_type": "choose_one"},
    )
    db.add(item)
    db.flush()
    step = ContentStep(item_id=item.id, order_index=1, prompt_text="اختبار")
    db.add(step)
    db.flush()
    return item, step


def _pending_audio(db, *, session_id: int, item: ContentItem, step: ContentStep, storage_key: str):
    item.interaction_type = "read_aloud"
    item.template_data = {"canonical_id": item.stable_key, "canonical_interaction_type": "read_aloud"}
    attempt = Attempt(session_id=session_id, item_id=item.id, status="completed")
    db.add(attempt)
    db.flush()
    response = AttemptResponse(
        attempt_id=attempt.id,
        step_id=step.id,
        selected_option_id=None,
        is_correct=None,
        elapsed_seconds=2,
    )
    db.add(response)
    db.flush()
    submission = AudioSubmission(
        response_id=response.id,
        storage_key=storage_key,
        file_size=100,
        mime_type="audio/webm",
        duration_seconds=2,
        status="uploaded",
    )
    db.add(submission)
    db.flush()
    return attempt, response, submission


def test_low_mastery_prepares_exact_skill_reinforcement_once_and_rewards_once():
    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        student.current_level = 1
        skill = Skill(skill_key="adaptive-skill-1", name="تمييز الحروف بصريًا", level_id=1)
        db.add(skill)
        db.flush()

        session = AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="in_progress",
            assigned_level=1,
        )
        db.add(session)
        db.flush()

        for index in range(1, 4):
            item, step = _item(
                db,
                stable_key=f"CORE-{index}",
                kind="core_activity",
                skill_id=skill.id,
                order_index=index,
            )
            attempt = Attempt(session_id=session.id, item_id=item.id, status="completed")
            db.add(attempt)
            db.flush()
            db.add(ActivityStepResponse(
                attempt_id=attempt.id,
                step_id=step.id,
                attempt_no=1,
                response_payload={"selected_option_ids": [999]},
                is_correct=False,
                hint_used=False,
                elapsed_seconds=3,
            ))

        # Unresolved audio is deliberately present while three already-graded
        # failures justify same-level support. It must not suppress adaptation.
        pending_item, pending_step = _item(
            db,
            stable_key="CORE-PENDING-AUDIO",
            kind="core_activity",
            skill_id=skill.id,
            order_index=4,
        )
        _pending_audio(
            db,
            session_id=session.id,
            item=pending_item,
            step=pending_step,
            storage_key="test/support-pending.webm",
        )

        reinforcement, _ = _item(
            db,
            stable_key="REIN-1",
            kind="reinforcement_activity",
            skill_id=skill.id,
            order_index=1,
        )
        db.commit()

        first = prepare_next_for_student(db, student, session)
        assert first["decision"]["action"] == "support"
        assert first["decision"]["mastery_score"] == 0.0
        assert first["decision"]["recommended_item_id"] == reinforcement.id
        assert first["recommended_attempt_id"] is not None

        second = prepare_next_for_student(db, student, session)
        assert second["decision"]["decision_id"] == first["decision"]["decision_id"]
        assert second["recommended_attempt_id"] == first["recommended_attempt_id"]
        assert db.query(Attempt).filter(
            Attempt.session_id == session.id,
            Attempt.item_id == reinforcement.id,
        ).count() == 1

        first_rewards = ensure_rewards(db, student.id)
        second_rewards = ensure_rewards(db, student.id)
        stars = [reward for reward in first_rewards if reward.reward_type == "stars"]
        assert len(stars) == 3
        assert all(reward.stars == 3 for reward in stars)
        assert len(second_rewards) == len(first_rewards)
    finally:
        db.close()


def test_declared_media_gap_is_neutral_not_a_false_failure():
    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        student.current_level = 1
        skill = Skill(skill_key="adaptive-gap-skill", name="مهارة فجوة الوسائط", level_id=1)
        db.add(skill)
        db.flush()
        session = AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="in_progress",
            assigned_level=1,
        )
        db.add(session)
        db.flush()

        item, step = _item(
            db,
            stable_key="CORE-GAP",
            kind="core_activity",
            skill_id=skill.id,
            order_index=1,
        )
        attempt = Attempt(session_id=session.id, item_id=item.id, status="completed")
        db.add(attempt)
        db.flush()
        db.add(ActivityStepResponse(
            attempt_id=attempt.id,
            step_id=step.id,
            attempt_no=1,
            response_payload={"declared_media_gap_skip": True},
            is_correct=True,
            hint_used=False,
            elapsed_seconds=0,
        ))
        db.commit()

        # A gap-only attempt contains no scorable evidence, so it must not count
        # as one of the three valid adaptation attempts or earn a fixed reward.
        result = prepare_next_for_student(db, student, session)
        assert result["decision"]["ready"] is False
        assert result["decision"]["valid_attempt_count"] == 0
        assert ensure_rewards(db, student.id) == []
    finally:
        db.close()


def test_unresolved_audio_completion_is_neutral_until_reviewed():
    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        student.current_level = 1
        skill = Skill(skill_key="adaptive-audio-skill", name="قراءة صوتية", level_id=1)
        db.add(skill)
        db.flush()
        session = AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="in_progress",
            assigned_level=1,
        )
        db.add(session)
        db.flush()

        item, step = _item(
            db,
            stable_key="CORE-AUDIO",
            kind="core_activity",
            skill_id=skill.id,
            order_index=1,
        )
        _, response, submission = _pending_audio(
            db,
            session_id=session.id,
            item=item,
            step=step,
            storage_key="test/unresolved.webm",
        )
        db.commit()

        assert ensure_rewards(db, student.id) == []
        unresolved = prepare_next_for_student(db, student, session)
        assert unresolved["decision"]["ready"] is False
        assert unresolved["decision"]["valid_attempt_count"] == 0

        # Immutable rejected history remains, but the newest graded rerecord is
        # the only review state allowed to become academic evidence.
        submission.status = "rerecord_required"
        db.add(AudioSubmission(
            response_id=response.id,
            storage_key="test/rerecorded-graded.webm",
            file_size=110,
            mime_type="audio/webm",
            duration_seconds=2,
            status="graded",
        ))
        response.is_correct = True
        db.commit()
        graded = prepare_next_for_student(db, student, session)
        assert graded["decision"]["ready"] is False
        assert graded["decision"]["valid_attempt_count"] == 1
        assert len([reward for reward in ensure_rewards(db, student.id) if reward.reward_type == "stars"]) == 1
    finally:
        db.close()


def test_unresolved_audio_holds_promotion_boundary_until_latest_submission_is_graded(monkeypatch):
    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        student.current_level = 1
        skill = Skill(skill_key="adaptive-promotion-audio", name="قراءة صوتية للترقية", level_id=1)
        db.add(skill)
        db.flush()
        session = AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="in_progress",
            assigned_level=1,
        )
        db.add(session)
        db.flush()

        item, step = _item(
            db,
            stable_key="CORE-PROMOTION-AUDIO",
            kind="core_activity",
            skill_id=skill.id,
            order_index=1,
        )
        _, response, submission = _pending_audio(
            db,
            session_id=session.id,
            item=item,
            step=step,
            storage_key="test/promotion-pending.webm",
        )
        decision = AdaptationDecision(
            student_id=student.id,
            decision_source="automatic",
            action="promote",
            mastery_score=90,
            previous_level=1,
            new_level=2,
            weakest_skill_id=skill.id,
            recommended_item_id=None,
            valid_attempt_count=6,
            consecutive_low_count=0,
            snapshot_key="test:promotion:pending-audio",
            explanation={"reason": "early_promotion_gates_passed"},
        )
        db.add(decision)
        db.commit()

        payload = {
            "ready": True,
            "decision_id": decision.id,
            "action": "promote",
            "mastery_score": 90.0,
            "previous_level": 1,
            "new_level": 2,
            "recommended_item_id": None,
            "valid_attempt_count": 6,
        }
        monkeypatch.setattr(adaptation_runtime, "evaluate_student", lambda *_args, **_kwargs: payload)

        held = prepare_next_for_student(db, student, session)
        assert held["decision"]["action"] == "hold"
        assert held["decision"]["reason"] == "unresolved_audio_evidence"
        assert held["decision"]["pending_audio_reviews"] == 1
        assert held["level_transitioned"] is False
        assert student.current_level == 1
        assert session.status == "in_progress"

        submission.status = "graded"
        response.is_correct = True
        db.commit()
        promoted = prepare_next_for_student(db, student, session)
        assert promoted["level_transitioned"] is True
        assert promoted["level_id"] == 2
        assert student.current_level == 2
        assert session.status == "completed"
        assert db.query(AssessmentSession).filter(
            AssessmentSession.student_id == student.id,
            AssessmentSession.session_type == "core",
            AssessmentSession.assigned_level == 2,
            AssessmentSession.status == "in_progress",
        ).count() == 1
    finally:
        db.close()
