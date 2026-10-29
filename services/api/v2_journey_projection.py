"""Request-scoped, bounded V2 journey facts and the shared next-action policy.

A cohort page uses the same facts/resolver as one learner. Window functions
select only the current/official records; history and private answers are not
materialized. Nothing here writes academic evidence or caches learner data.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fastapi import HTTPException
from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session, aliased

from db.learning_models import (
    AssessmentQuestionResponse, LessonQuestionResponse, LessonSession,
    PlacementDecisionV2, StudentJourney, V2ReviewRetryTask,
)
from db.models import AssessmentRetakeAuthorization, AssessmentSession


def official_placement_query(db: Session, student_id, release_id, level):
    """One academic predicate, shared by lesson authorization and projections."""
    return db.query(PlacementDecisionV2.id).join(
        AssessmentSession, AssessmentSession.id == PlacementDecisionV2.assessment_session_id,
    ).filter(
        PlacementDecisionV2.student_id == student_id,
        PlacementDecisionV2.content_release_id == release_id,
        PlacementDecisionV2.assigned_level <= level,
        AssessmentSession.student_id == student_id,
        AssessmentSession.content_release_id == release_id,
        AssessmentSession.session_type == "pretest",
        AssessmentSession.status == "completed",
        AssessmentSession.v2_state == "completed",
        AssessmentSession.official_for_reporting.is_(True),
        AssessmentSession.assigned_level == PlacementDecisionV2.assigned_level,
    )


@dataclass
class JourneyFacts:
    student_id: int
    journey: StudentJourney | None = None
    assessments: dict[str, AssessmentSession] = field(default_factory=dict)
    active_assessment: AssessmentSession | None = None
    active_lesson: LessonSession | None = None
    eligible_lesson: bool = False
    prior_assessment: AssessmentSession | None = None
    retake_allowed: bool = False
    retry: dict[str, Any] | None = None
    completed_ids: set[str] = field(default_factory=set)
    placement_level: int | None = None


def _latest(db: Session, model, student_ids, *filters, order, partition=None):
    ranked = db.query(
        model.id.label("record_id"),
        func.row_number().over(
            partition_by=partition if partition is not None else model.student_id,
            order_by=order,
        ).label("position"),
    ).filter(model.student_id.in_(student_ids), *filters).subquery()
    return db.query(model).join(ranked, model.id == ranked.c.record_id).filter(ranked.c.position == 1).all()


def load_journey_facts(db: Session, student_ids: list[int]) -> dict[int, JourneyFacts]:
    """At most one page (50 accounts), with a fixed number of database queries."""
    if len(student_ids) > 50:
        raise ValueError("journey projection is limited to one 50-student page")
    facts = {student_id: JourneyFacts(student_id) for student_id in student_ids}
    if not facts:
        return facts
    for row in db.query(StudentJourney).filter(StudentJourney.student_id.in_(student_ids)).all():
        facts[row.student_id].journey = row

    # Prefer the active attempt, otherwise the latest official attempt per kind.
    for row in _latest(
        db, AssessmentSession, student_ids,
        AssessmentSession.v2_state.is_not(None),
        or_(AssessmentSession.status == "in_progress", AssessmentSession.official_for_reporting.is_(True)),
        AssessmentSession.session_type.in_(("pretest", "posttest")),
        partition=(AssessmentSession.student_id, AssessmentSession.session_type),
        order=(case((AssessmentSession.status == "in_progress", 0), else_=1),
               AssessmentSession.started_at.desc(), AssessmentSession.id.desc()),
    ):
        facts[row.student_id].assessments[row.session_type] = row
    for item in facts.values():
        active = [row for row in item.assessments.values() if row.status == "in_progress"]
        item.active_assessment = max(active, key=lambda row: (row.started_at, row.id)) if active else None

    for row in db.query(LessonSession).filter(
        LessonSession.student_id.in_(student_ids),
        LessonSession.status.in_(("in_progress", "waiting_review")),
    ).all():
        facts[row.student_id].active_lesson = row

    eligible = db.query(StudentJourney.student_id).filter(
        StudentJourney.student_id.in_(student_ids),
        StudentJourney.status == "active", StudentJourney.placement_state == "placed",
        official_placement_query(db, StudentJourney.student_id,
                                 StudentJourney.content_release_id, StudentJourney.current_level).exists(),
    ).all()
    for student_id, in eligible:
        facts[student_id].eligible_lesson = True

    # Only no-journey accounts need the V1 history/explicit-retake guard.
    unstarted = [student_id for student_id, item in facts.items() if item.journey is None]
    if unstarted:
        for row in _latest(db, AssessmentSession, unstarted, order=(AssessmentSession.id.desc(),)):
            facts[row.student_id].prior_assessment = row
        previous = _latest(
            db, AssessmentSession, unstarted, AssessmentSession.session_type == "pretest",
            order=(AssessmentSession.assessment_attempt_no.desc(), AssessmentSession.id.desc()),
        )
        if previous:
            previous_ids = [row.id for row in previous]
            # Match the previous session to its owner, even if malformed legacy
            # data contains a cross-account authorization reference.
            allowed_pairs = set(db.query(
                AssessmentRetakeAuthorization.student_id, AssessmentRetakeAuthorization.previous_session_id,
            ).filter(
                AssessmentRetakeAuthorization.student_id.in_(unstarted),
                AssessmentRetakeAuthorization.session_type == "pretest",
                AssessmentRetakeAuthorization.previous_session_id.in_(previous_ids),
                AssessmentRetakeAuthorization.status == "pending",
            ).all())
            for row in previous:
                facts[row.student_id].retake_allowed = (row.student_id, row.id) in allowed_pairs

    # Select minimal retry linkage, not replacement audio keys/private answers.
    ranked_retry = db.query(
        V2ReviewRetryTask.id.label("task_id"), V2ReviewRetryTask.student_id,
        V2ReviewRetryTask.lesson_response_id, V2ReviewRetryTask.assessment_response_id,
        func.row_number().over(partition_by=V2ReviewRetryTask.student_id,
                               order_by=V2ReviewRetryTask.id.asc()).label("position"),
    ).filter(V2ReviewRetryTask.student_id.in_(student_ids), V2ReviewRetryTask.status == "requested").subquery()
    lesson_owner = aliased(LessonSession)
    assessment_owner = aliased(AssessmentSession)
    retries = db.query(
        ranked_retry, LessonQuestionResponse.status.label("lesson_status"),
        LessonQuestionResponse.lesson_session_id, lesson_owner.student_id.label("lesson_owner"),
        AssessmentQuestionResponse.status.label("assessment_status"),
        AssessmentQuestionResponse.assessment_session_id, assessment_owner.student_id.label("assessment_owner"),
    ).outerjoin(LessonQuestionResponse, LessonQuestionResponse.id == ranked_retry.c.lesson_response_id).outerjoin(
        lesson_owner, lesson_owner.id == LessonQuestionResponse.lesson_session_id,
    ).outerjoin(AssessmentQuestionResponse, AssessmentQuestionResponse.id == ranked_retry.c.assessment_response_id).outerjoin(
        assessment_owner, assessment_owner.id == AssessmentQuestionResponse.assessment_session_id,
    ).filter(ranked_retry.c.position == 1).all()
    for row in retries:
        lesson = row.lesson_response_id is not None
        facts[row.student_id].retry = {
            "task_id": row.task_id, "kind": "lesson" if lesson else "assessment",
            "status": row.lesson_status if lesson else row.assessment_status,
            "session_id": row.lesson_session_id if lesson else row.assessment_session_id,
            "owner_id": row.lesson_owner if lesson else row.assessment_owner,
        }

    # Progress is distinct completed lessons within each student's pinned bank.
    completed = db.query(LessonSession.student_id, LessonSession.lesson_id).join(
        StudentJourney, StudentJourney.student_id == LessonSession.student_id,
    ).filter(
        LessonSession.student_id.in_(student_ids), LessonSession.status == "completed",
        LessonSession.content_release_id == StudentJourney.content_release_id,
    ).distinct().all()
    for student_id, lesson_id in completed:
        facts[student_id].completed_ids.add(lesson_id)
    # Latest placement per student/release; no historical decision list loaded.
    placement_ids = db.query(
        PlacementDecisionV2.student_id, func.max(PlacementDecisionV2.id).label("latest_id"),
    ).join(StudentJourney, StudentJourney.student_id == PlacementDecisionV2.student_id).filter(
        PlacementDecisionV2.student_id.in_(student_ids),
        PlacementDecisionV2.content_release_id == StudentJourney.content_release_id,
    ).group_by(PlacementDecisionV2.student_id).subquery()
    for student_id, level in db.query(PlacementDecisionV2.student_id, PlacementDecisionV2.assigned_level).join(
        placement_ids, PlacementDecisionV2.id == placement_ids.c.latest_id,
    ).all():
        facts[student_id].placement_level = level
    return facts


def next_action(facts: JourneyFacts) -> dict[str, Any]:
    """One policy for the learner home/current-action and staff list/dashboard."""
    retry = facts.retry
    if retry is not None:
        if retry["status"] != "pending_review":
            raise HTTPException(status_code=409, detail="طلب إعادة القراءة بحاجة إلى مراجعة المشرف")
        if retry["session_id"] is None or retry["owner_id"] != facts.student_id:
            raise HTTPException(status_code=409, detail="تعذر ربط طلب القراءة بجلسة الطالب")
        return {"action": "rerecord_required", "state": "requested", "task_id": retry["task_id"],
                "kind": retry["kind"], "session_id": retry["session_id"],
                "href": f'/student/retry/{retry["task_id"]}', "label": "أعد تسجيل القراءة"}
    assessment = facts.active_assessment
    if assessment:
        return {"action": "assessment", "kind": assessment.session_type, "state": assessment.v2_state,
                "href": f"/student/assessment-v2/{assessment.id}",
                "label": "متابعة الاختبار" if assessment.v2_state == "answering" else "عرض حالة المراجعة"}
    journey, lesson = facts.journey, facts.active_lesson
    if facts.eligible_lesson and lesson and lesson.content_release_id == journey.content_release_id:
        return {"action": "lesson", "state": lesson.stage,
                "href": f"/student/learning-v2/{lesson.id}", "label": "متابعة الدرس"}
    if not journey and facts.prior_assessment:
        if facts.prior_assessment.status == "in_progress" or not facts.retake_allowed:
            return {"action": "migration_review", "href": None, "label": "بانتظار مراجعة المشرف"}
    if not journey or journey.placement_state in {"not_started", "in_progress"}:
        return {"action": "start_pretest", "href": None, "label": "ابدأ الاختبار القبلي"}
    if journey.placement_state == "placed" and not facts.eligible_lesson:
        return {"action": "placement_review", "href": None, "label": "بانتظار مراجعة المشرف"}
    if journey.placement_state == "posttest_ready":
        return {"action": "start_posttest", "href": None, "label": "ابدأ الاختبار البعدي"}
    if journey.placement_state == "completed":
        return {"action": "complete", "href": "/student/learning-v2", "label": "اكتملت الرحلة"}
    return {"action": "lesson_catalog", "href": "/student/learning-v2", "label": "متابعة الرحلة التعليمية"}
