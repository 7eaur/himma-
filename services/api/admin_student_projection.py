"""Batched, read-only projection for the supervisor student list.

The list endpoint must not rebuild the full student journey one learner at a
time. This module loads the durable evidence needed by ``StudentResponse`` in a
bounded set of queries, while preserving the same academic completion rules as
``level_completion.py``:

- ten completed Core activities complete any level;
- L1/L2 may complete through an automatic promotion tied to that exact session;
- L3 requires ten completed Core activities;
- an active Core session keeps the learning journey open;
- the latest pretest attempt must itself be completed before the journey can be
  treated as complete for posttest eligibility.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from sqlalchemy import func
from sqlalchemy.orm import Session

from db.adaptation_models import AdaptationDecision
from db.models import AssessmentSession, Attempt, ContentItem, Student
from level_completion import CORE_ACTIVITY_COUNT


def _promotion_session_ids(
    db: Session,
    *,
    student_ids: list[int],
    candidate_session_ids: set[int],
) -> set[int]:
    if not candidate_session_ids:
        return set()

    promoted: set[int] = set()
    decisions = (
        db.query(AdaptationDecision)
        .filter(
            AdaptationDecision.student_id.in_(student_ids),
            AdaptationDecision.decision_source == "automatic",
            AdaptationDecision.action == "promote",
        )
        .all()
    )
    for decision in decisions:
        explanation = decision.explanation or {}
        previous_session_id = explanation.get("previous_session_id")
        if previous_session_id not in candidate_session_ids:
            continue
        expected_transition = f"L{decision.previous_level}->L{decision.new_level}"
        if (
            decision.previous_level in {1, 2}
            and decision.new_level == decision.previous_level + 1
            and explanation.get("journey_transition") == expected_transition
        ):
            promoted.add(int(previous_session_id))
    return promoted


def build_student_list_payloads(
    db: Session,
    students: Iterable[Student],
) -> list[dict]:
    """Return ``StudentResponse`` payloads with query count independent of cohort size."""
    student_list = list(students)
    if not student_list:
        return []

    student_ids = [int(student.id) for student in student_list]
    sessions = (
        db.query(AssessmentSession)
        .filter(
            AssessmentSession.student_id.in_(student_ids),
            AssessmentSession.session_type.in_(("pretest", "posttest", "core")),
        )
        .order_by(AssessmentSession.id)
        .all()
    )

    latest_pretest: dict[int, AssessmentSession] = {}
    posttest_completed: set[int] = set()
    core_by_student: dict[int, list[AssessmentSession]] = defaultdict(list)
    core_session_ids: list[int] = []

    for session in sessions:
        student_id = int(session.student_id)
        if session.session_type == "pretest":
            latest_pretest[student_id] = session
        elif session.session_type == "posttest":
            if session.status == "completed":
                posttest_completed.add(student_id)
        elif session.session_type == "core":
            core_by_student[student_id].append(session)
            core_session_ids.append(int(session.id))

    completed_counts: dict[tuple[int, int], int] = {}
    if core_session_ids:
        rows = (
            db.query(
                Attempt.session_id,
                ContentItem.level_id,
                func.count(func.distinct(ContentItem.id)),
            )
            .join(ContentItem, ContentItem.id == Attempt.item_id)
            .filter(
                Attempt.session_id.in_(core_session_ids),
                Attempt.status == "completed",
                ContentItem.kind == "core_activity",
            )
            .group_by(Attempt.session_id, ContentItem.level_id)
            .all()
        )
        completed_counts = {
            (int(session_id), int(level_id)): int(count)
            for session_id, level_id, count in rows
        }

    promotion_candidates: set[int] = set()
    for student_sessions in core_by_student.values():
        for session in student_sessions:
            level_id = int(session.assigned_level or 0)
            count = completed_counts.get((int(session.id), level_id), 0)
            if (
                session.status == "completed"
                and level_id in {1, 2}
                and count < CORE_ACTIVITY_COUNT
            ):
                promotion_candidates.add(int(session.id))

    promoted_session_ids = _promotion_session_ids(
        db,
        student_ids=student_ids,
        candidate_session_ids=promotion_candidates,
    )

    def completion(session: AssessmentSession) -> tuple[int, bool]:
        level_id = int(session.assigned_level or 0)
        if session.session_type != "core" or level_id not in {1, 2, 3}:
            return 0, False
        count = completed_counts.get((int(session.id), level_id), 0)
        if session.status != "completed":
            return count, False
        if count >= CORE_ACTIVITY_COUNT:
            return count, True
        return count, int(session.id) in promoted_session_ids

    payloads: list[dict] = []
    for student in student_list:
        student_id = int(student.id)
        student_core = core_by_student.get(student_id, [])
        latest_core = student_core[-1] if student_core else None
        latest_core_count, latest_core_completed = (
            completion(latest_core) if latest_core is not None else (0, False)
        )

        latest_pretest_session = latest_pretest.get(student_id)
        any_completed_pretest = any(
            session.student_id == student_id
            and session.session_type == "pretest"
            and session.status == "completed"
            for session in sessions
        )
        journey_pretest_completed = bool(
            latest_pretest_session is not None
            and latest_pretest_session.status == "completed"
        )
        active_core_exists = any(session.status == "in_progress" for session in student_core)
        level3_completed = any(
            int(session.assigned_level or 0) == 3 and completion(session)[1]
            for session in student_core
        )
        learning_journey_completed = (
            journey_pretest_completed
            and level3_completed
            and not active_core_exists
        )
        has_completed_posttest = student_id in posttest_completed

        payloads.append(
            {
                "id": student.id,
                "full_name": student.name,
                "access_code": student.access_code,
                "grade_level": student.grade_level,
                "current_level": student.current_level,
                "status": "active" if student.is_active else "inactive",
                "posttest_enabled": student.posttest_enabled,
                "posttest_eligible": (
                    any_completed_pretest
                    and learning_journey_completed
                    and not has_completed_posttest
                ),
                "core_completed_items": latest_core_count,
                "core_total_items": CORE_ACTIVITY_COUNT,
                "core_completed": latest_core_completed,
                "created_at": student.created_at,
            }
        )

    return payloads
