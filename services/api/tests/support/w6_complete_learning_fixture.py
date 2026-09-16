"""Advance one already-assessed W6 candidate through durable learning evidence.

This test-only accelerator exists to keep the final browser journey bounded: the
browser proves the real pretest, recording/review flow, learning entry, posttest
authorization and real posttest UI on one identity, while the long middle
learning history is persisted with the exact canonical completion evidence used
by Journey/Rewards. Production transition rules remain covered independently by
M09 and the adaptation/level-completion suites.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[2]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from db.adaptation_models import AdaptationDecision  # noqa: E402
from db.database import SessionLocal  # noqa: E402
from db.models import AssessmentSession, Attempt, ContentItem, Student  # noqa: E402
from journey import build_journey_summary  # noqa: E402


def _core_items(db, level_id: int) -> list[ContentItem]:
    items = (
        db.query(ContentItem)
        .filter(ContentItem.kind == "core_activity", ContentItem.level_id == level_id)
        .order_by(ContentItem.order_index, ContentItem.id)
        .all()
    )
    if len(items) != 10:
        raise RuntimeError(f"Expected 10 canonical Core items for L{level_id}, got {len(items)}")
    return items


def _session_for_level(db, student: Student, level_id: int) -> AssessmentSession:
    session = (
        db.query(AssessmentSession)
        .filter(
            AssessmentSession.student_id == student.id,
            AssessmentSession.session_type == "core",
            AssessmentSession.assigned_level == level_id,
        )
        .order_by(AssessmentSession.id.desc())
        .first()
    )
    if session is None:
        session = AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="in_progress",
            assigned_level=level_id,
        )
        db.add(session)
        db.flush()
    return session


def _complete_items(db, session: AssessmentSession, items: list[ContentItem]) -> None:
    now = datetime.now(timezone.utc)
    existing = {
        attempt.item_id: attempt
        for attempt in db.query(Attempt).filter(Attempt.session_id == session.id).all()
    }
    for item in items:
        attempt = existing.get(item.id)
        if attempt is None:
            attempt = Attempt(session_id=session.id, item_id=item.id)
            db.add(attempt)
            db.flush()
        attempt.status = "completed"
        attempt.completed_at = attempt.completed_at or now
        attempt.elapsed_seconds = max(int(attempt.elapsed_seconds or 0), 1)
    db.flush()


def _close_with_early_promotion(db, student: Student, session: AssessmentSession, level_id: int) -> None:
    if level_id not in {1, 2}:
        raise RuntimeError("Early-promotion evidence is valid only for L1/L2")
    _complete_items(db, session, _core_items(db, level_id)[:6])
    now = datetime.now(timezone.utc)
    session.status = "completed"
    session.completed_at = session.completed_at or now
    session.updated_at = now
    db.flush()

    transition = f"L{level_id}->L{level_id + 1}"
    existing = db.query(AdaptationDecision.id).filter(
        AdaptationDecision.student_id == student.id,
        AdaptationDecision.decision_source == "automatic",
        AdaptationDecision.action == "promote",
        AdaptationDecision.previous_level == level_id,
        AdaptationDecision.new_level == level_id + 1,
    ).first()
    if existing is None:
        db.add(AdaptationDecision(
            student_id=student.id,
            decision_source="automatic",
            action="promote",
            mastery_score=95,
            previous_level=level_id,
            new_level=level_id + 1,
            weakest_skill_id=None,
            recommended_item_id=None,
            valid_attempt_count=6,
            consecutive_low_count=0,
            snapshot_key=f"w6-longitudinal-L{level_id}-{session.id}",
            explanation={
                "policy_version": "HIMMA_ADAPTIVE_V4_PILOT",
                "reason": "early_promotion_gates_passed",
                "previous_session_id": session.id,
                "journey_transition": transition,
                "completed_core_count": 6,
                "fixture_scope": "w6_longitudinal_browser_acceptance",
            },
        ))
    student.current_level = level_id + 1
    db.flush()


def main() -> None:
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        raise SystemExit("usage: w6_complete_learning_fixture.py STUDENT_ID")
    student_id = int(sys.argv[1])

    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.id == student_id).one()
        pretest = db.query(AssessmentSession).filter(
            AssessmentSession.student_id == student.id,
            AssessmentSession.session_type == "pretest",
            AssessmentSession.status == "completed",
        ).order_by(AssessmentSession.id.desc()).first()
        if pretest is None:
            raise RuntimeError("W6 longitudinal accelerator requires a completed live pretest")

        start_level = int(student.current_level)
        if start_level not in {1, 2, 3}:
            raise RuntimeError(f"Unexpected current level {start_level}")

        for level_id in range(start_level, 3):
            session = _session_for_level(db, student, level_id)
            _close_with_early_promotion(db, student, session, level_id)
            db.flush()

        level3 = _session_for_level(db, student, 3)
        _complete_items(db, level3, _core_items(db, 3))
        now = datetime.now(timezone.utc)
        level3.status = "completed"
        level3.completed_at = level3.completed_at or now
        level3.updated_at = now
        student.current_level = 3
        student.posttest_enabled = False
        student.posttest_enabled_at = None
        student.posttest_enabled_by = None
        db.commit()

        db.refresh(student)
        journey = build_journey_summary(db, student)
        if not journey["learning_journey_completed"]:
            raise RuntimeError(f"Learning journey did not close: {journey}")

        print(json.dumps({
            "student_id": student.id,
            "starting_level": journey["starting_level"],
            "current_level": student.current_level,
            "level_states": [level["state"] for level in journey["levels"]],
            "learning_journey_completed": journey["learning_journey_completed"],
            "posttest_enabled": student.posttest_enabled,
            "posttest_completed": journey["posttest_completed"],
        }, ensure_ascii=False))
    finally:
        db.close()


if __name__ == "__main__":
    main()
