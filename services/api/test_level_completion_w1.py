"""W1 regression coverage for the single canonical Level Completion owner."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

import seed_all
from adaptation import ensure_rewards
from db.adaptation_models import AdaptationDecision, RewardEvent
from db.database import SessionLocal
from db.models import AssessmentSession, Attempt, ContentItem, Student
from level_completion import session_level_completion
from protected import _core_progress


def _student(db) -> Student:
    return db.query(Student).filter(Student.access_code == "STU001").one()


def _completed_core_session(db, *, level_id: int, core_count: int) -> AssessmentSession:
    student = _student(db)
    session = AssessmentSession(
        student_id=student.id,
        session_type="core",
        status="completed",
        assigned_level=level_id,
        completed_at=datetime.now(timezone.utc),
    )
    db.add(session)
    db.flush()
    items = (
        db.query(ContentItem)
        .filter(
            ContentItem.kind == "core_activity",
            ContentItem.level_id == level_id,
            ContentItem.status == "approved",
        )
        .order_by(ContentItem.order_index, ContentItem.id)
        .limit(core_count)
        .all()
    )
    assert len(items) == core_count
    for item in items:
        db.add(Attempt(
            session_id=session.id,
            item_id=item.id,
            status="completed",
            completed_at=datetime.now(timezone.utc),
        ))
    db.flush()
    return session


def _automatic_promotion(db, *, session: AssessmentSession, level_id: int) -> AdaptationDecision:
    decision = AdaptationDecision(
        student_id=session.student_id,
        decision_source="automatic",
        action="promote",
        mastery_score=Decimal("90.0"),
        previous_level=level_id,
        new_level=level_id + 1,
        valid_attempt_count=6,
        consecutive_low_count=0,
        snapshot_key=f"w1-early-promotion-{session.id}",
        explanation={
            "policy_version": "HIMMA_ADAPTIVE_V4_PILOT",
            "reason": "early_promotion_gates_passed",
            "previous_session_id": session.id,
            "journey_transition": f"L{level_id}->L{level_id + 1}",
        },
    )
    db.add(decision)
    db.flush()
    return decision


def _badge_exists(db, student_id: int, level_id: int) -> bool:
    return db.query(RewardEvent.id).filter(
        RewardEvent.student_id == student_id,
        RewardEvent.reward_key == f"level:{level_id}:core-complete",
        RewardEvent.reward_type == "badge",
    ).first() is not None


@pytest.mark.parametrize("core_count", [6, 7, 8, 9])
def test_l1_early_promotion_6_to_9_core_is_canonical_completion_and_badge(core_count):
    seed_all.run_seed_all()
    db = SessionLocal()
    try:
        session = _completed_core_session(db, level_id=1, core_count=core_count)
        _automatic_promotion(db, session=session, level_id=1)
        db.commit()

        evidence = session_level_completion(db, session)
        assert evidence.completed is True
        assert evidence.completed_core_count == core_count
        assert evidence.method == "automatic_early_promotion"

        admin_count, admin_complete = _core_progress(db, session.student_id)
        assert admin_count == core_count
        assert admin_complete is True

        ensure_rewards(db, session.student_id)
        assert _badge_exists(db, session.student_id, 1) is True
    finally:
        db.close()


def test_manual_override_does_not_create_level_completion_or_badge():
    seed_all.run_seed_all()
    db = SessionLocal()
    try:
        session = _completed_core_session(db, level_id=1, core_count=6)
        db.add(AdaptationDecision(
            student_id=session.student_id,
            decision_source="manual",
            action="override",
            mastery_score=None,
            previous_level=1,
            new_level=2,
            valid_attempt_count=0,
            consecutive_low_count=0,
            snapshot_key=None,
            explanation={
                "reason": "supervisor_manual_override",
                "previous_session_id": session.id,
                "journey_transition": "L1->L2",
            },
            manual_reason="قرار يدوي للاختبار لا يمثل إكمالًا أكاديميًا",
        ))
        db.commit()

        evidence = session_level_completion(db, session)
        assert evidence.completed is False
        assert evidence.completed_core_count == 6
        assert evidence.method is None

        admin_count, admin_complete = _core_progress(db, session.student_id)
        assert admin_count == 6
        assert admin_complete is False

        ensure_rewards(db, session.student_id)
        assert _badge_exists(db, session.student_id, 1) is False
    finally:
        db.close()


def test_level_three_requires_all_ten_core_before_completion_or_badge():
    seed_all.run_seed_all()
    db = SessionLocal()
    try:
        session = _completed_core_session(db, level_id=3, core_count=9)
        db.commit()

        evidence = session_level_completion(db, session)
        assert evidence.completed is False
        assert evidence.completed_core_count == 9
        ensure_rewards(db, session.student_id)
        assert _badge_exists(db, session.student_id, 3) is False

        tenth = (
            db.query(ContentItem)
            .filter(
                ContentItem.kind == "core_activity",
                ContentItem.level_id == 3,
                ContentItem.status == "approved",
            )
            .order_by(ContentItem.order_index, ContentItem.id)
            .offset(9)
            .first()
        )
        assert tenth is not None
        db.add(Attempt(
            session_id=session.id,
            item_id=tenth.id,
            status="completed",
            completed_at=datetime.now(timezone.utc),
        ))
        db.commit()

        evidence = session_level_completion(db, session)
        assert evidence.completed is True
        assert evidence.completed_core_count == 10
        assert evidence.method == "full_core"
        ensure_rewards(db, session.student_id)
        assert _badge_exists(db, session.student_id, 3) is True
    finally:
        db.close()
