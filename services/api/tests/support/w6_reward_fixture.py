"""Create deterministic W6 completion evidence without pre-awarding a reward.

This helper is test-only setup for the browser acceptance. It persists the same
canonical durable evidence consumed by ``level_completion``: a completed L1
Core session plus an automatic L1->L2 promotion decision tied to that session.
The live `/rewards` endpoint must be the first component that materializes the
badge, allowing the browser test to prove award, canonical asset projection,
Student/Admin presentation, refresh persistence and idempotency.
"""
from __future__ import annotations

import json
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[2]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from db.adaptation_models import AdaptationDecision, RewardEvent  # noqa: E402
from db.database import SessionLocal  # noqa: E402
from db.models import AssessmentSession, Student  # noqa: E402


def _unused_access_code(db) -> str:
    for _ in range(100):
        code = f"{secrets.randbelow(1_000_000):06d}"
        if db.query(Student.id).filter(Student.access_code == code).first() is None:
            return code
    raise RuntimeError("Unable to allocate a unique W6 access code")


def main() -> None:
    db = SessionLocal()
    try:
        code = _unused_access_code(db)
        student = Student(
            access_code=code,
            name=f"طالب قبول المكافآت {code}",
            grade_level=3,
            current_level=2,
            is_active=True,
        )
        db.add(student)
        db.flush()

        now = datetime.now(timezone.utc)
        completed_l1 = AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="completed",
            assigned_level=1,
            completed_at=now,
            updated_at=now,
        )
        db.add(completed_l1)
        db.flush()

        decision = AdaptationDecision(
            student_id=student.id,
            decision_source="automatic",
            action="promote",
            mastery_score=95,
            previous_level=1,
            new_level=2,
            weakest_skill_id=None,
            recommended_item_id=None,
            valid_attempt_count=6,
            consecutive_low_count=0,
            snapshot_key=f"w6-reward-{student.id}",
            explanation={
                "policy_version": "HIMMA_ADAPTIVE_V4_PILOT",
                "reason": "early_promotion_gates_passed",
                "previous_session_id": completed_l1.id,
                "journey_transition": "L1->L2",
                "completed_core_count": 6,
                "fixture_scope": "w6_browser_acceptance",
            },
        )
        db.add(decision)
        db.commit()

        reward_count_before = db.query(RewardEvent.id).filter(RewardEvent.student_id == student.id).count()
        if reward_count_before != 0:
            raise RuntimeError("W6 fixture must not pre-award rewards")

        print(json.dumps({
            "student_id": student.id,
            "access_code": code,
            "name": student.name,
            "reward_count_before": reward_count_before,
            "completion_session_id": completed_l1.id,
            "promotion_decision_id": decision.id,
        }, ensure_ascii=False))
    finally:
        db.close()


if __name__ == "__main__":
    main()
