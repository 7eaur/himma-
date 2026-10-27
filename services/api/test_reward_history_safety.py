"""Regression coverage for durable reward history across attempt cleanup."""

from sqlalchemy import text

import seed_all
from db.adaptation_models import RewardEvent
from db.database import SessionLocal
from db.models import AssessmentSession, Attempt, ContentItem, Student


def test_attempt_cleanup_preserves_reward_and_nulls_optional_evidence_pointer():
    seed_all.run_seed_all()
    db = SessionLocal()
    try:
        if db.bind is not None and db.bind.dialect.name == "sqlite":
            # SQLite does not enable FK actions by default; production/CI uses
            # PostgreSQL, but local fallback should exercise the same contract.
            db.execute(text("PRAGMA foreign_keys=ON"))

        student = db.query(Student).filter(Student.access_code == "STU001").one()
        item = (
            db.query(ContentItem)
            .filter(ContentItem.kind == "core_activity", ContentItem.status == "approved")
            .order_by(ContentItem.id)
            .first()
        )
        assert item is not None

        session = AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="completed",
            assigned_level=item.level_id,
        )
        db.add(session)
        db.flush()
        attempt = Attempt(
            session_id=session.id,
            item_id=item.id,
            status="completed",
        )
        db.add(attempt)
        db.flush()
        reward = RewardEvent(
            student_id=student.id,
            attempt_id=attempt.id,
            reward_type="stars",
            reward_key="history-safety:test-stars",
            stars=3,
            label="نجوم محفوظة",
            details={"source": "history-safety-regression"},
        )
        db.add(reward)
        db.commit()
        reward_id = reward.id

        db.delete(attempt)
        db.commit()
        db.expire_all()

        preserved = db.get(RewardEvent, reward_id)
        assert preserved is not None
        assert preserved.attempt_id is None
        assert preserved.reward_key == "history-safety:test-stars"
        assert preserved.stars == 3
        assert preserved.details == {"source": "history-safety-regression"}
    finally:
        db.close()
