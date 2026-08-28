"""Research reporting endpoints for M07.

This module reports persisted academic/runtime evidence. It deliberately does not
recalculate placement or adaptation rules, and it does not invent speech-derived
metrics when calibrated speech evidence is unavailable.
"""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.models import AssessmentSession, Attempt, Student, User
from db.reinforcement_models import ReinforcementCycle
from dependencies import get_current_user, get_db

router = APIRouter(prefix="/researcher/reports", tags=["Research Reports"])


def _number(value) -> float | None:
    if value is None:
        return None
    return float(value)


def _improvement(pre_score: float | None, post_score: float | None) -> tuple[float | None, float | None]:
    """Return percentage-point and relative improvements without inventing zero baselines."""
    if pre_score is None or post_score is None:
        return None, None
    absolute = round(post_score - pre_score, 4)
    relative = None if pre_score == 0 else round((absolute / pre_score) * 100.0, 4)
    return absolute, relative


def _sessions_by_type(db: Session, student_id: int) -> dict[str, AssessmentSession | None]:
    rows = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student_id,
        AssessmentSession.session_type.in_(["pretest", "posttest"]),
    ).order_by(AssessmentSession.id).all()
    result: dict[str, AssessmentSession | None] = {"pretest": None, "posttest": None}
    for row in rows:
        result[row.session_type] = row
    return result


def build_student_research_report(db: Session, student: Student) -> dict:
    sessions = _sessions_by_type(db, student.id)
    pre = sessions["pretest"]
    post = sessions["posttest"]

    pre_score = _number(pre.final_score) if pre and pre.status == "completed" else None
    post_score = _number(post.final_score) if post and post.status == "completed" else None
    absolute_improvement, relative_improvement = _improvement(pre_score, post_score)

    core_sessions = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student.id,
        AssessmentSession.session_type == "core",
    ).order_by(AssessmentSession.id).all()
    all_session_ids = [session.id for session in [pre, post, *core_sessions] if session is not None]
    attempt_count = 0
    completed_attempt_count = 0
    if all_session_ids:
        attempt_count = db.query(func.count(Attempt.id)).filter(Attempt.session_id.in_(all_session_ids)).scalar() or 0
        completed_attempt_count = db.query(func.count(Attempt.id)).filter(
            Attempt.session_id.in_(all_session_ids),
            Attempt.status == "completed",
        ).scalar() or 0

    cycles = db.query(ReinforcementCycle).filter(
        ReinforcementCycle.student_id == student.id,
    ).order_by(ReinforcementCycle.id).all()
    cycle_counts = {
        "total": len(cycles),
        "verified": sum(1 for cycle in cycles if cycle.status == "verified"),
        "escalated": sum(1 for cycle in cycles if cycle.status == "escalated"),
        "active": sum(1 for cycle in cycles if cycle.status not in {"verified", "escalated"}),
    }

    completed_core_levels = [
        int(session.assigned_level)
        for session in core_sessions
        if session.status == "completed" and session.assigned_level is not None
    ]

    return {
        "student_id": student.id,
        "student_name": student.name,
        "status": "active" if student.is_active else "inactive",
        "starting_level": int(pre.assigned_level) if pre and pre.status == "completed" and pre.assigned_level else None,
        "current_level": student.current_level,
        "final_level": int(post.assigned_level) if post and post.status == "completed" and post.assigned_level else None,
        "completed_core_levels": completed_core_levels,
        "pretest": {
            "status": pre.status if pre else "not_started",
            "score": pre_score,
            "elapsed_seconds": pre.elapsed_seconds if pre else 0,
            "completed_at": pre.completed_at if pre else None,
        },
        "posttest": {
            "status": post.status if post else "not_started",
            "score": post_score,
            "elapsed_seconds": post.elapsed_seconds if post else 0,
            "completed_at": post.completed_at if post else None,
        },
        "improvement": {
            "absolute_percentage_points": absolute_improvement,
            "relative_percent": relative_improvement,
            "relative_percent_defined": relative_improvement is not None,
        },
        "engagement": {
            "assessment_seconds": (pre.elapsed_seconds if pre else 0) + (post.elapsed_seconds if post else 0),
            "learning_seconds": sum(session.elapsed_seconds for session in core_sessions),
            "attempts": int(attempt_count),
            "completed_attempts": int(completed_attempt_count),
        },
        "reinforcement": cycle_counts,
        "speech_evidence": {
            "calibrated": False,
            "error_categories": None,
            "note": "لا تُعرض أخطاء نطق آلية قبل وجود دليل صوتي مُعاير ومعتمد.",
        },
    }


def build_cohort_research_report(db: Session) -> dict:
    students = db.query(Student).order_by(Student.id).all()
    reports = [build_student_research_report(db, student) for student in students]

    paired = [
        report for report in reports
        if report["pretest"]["score"] is not None and report["posttest"]["score"] is not None
    ]
    pre_scores = [report["pretest"]["score"] for report in reports if report["pretest"]["score"] is not None]
    post_scores = [report["posttest"]["score"] for report in reports if report["posttest"]["score"] is not None]
    improvements = [report["improvement"]["absolute_percentage_points"] for report in paired]

    def avg(values: list[float]) -> float | None:
        return round(sum(values) / len(values), 4) if values else None

    return {
        "cohort": {
            "students": len(reports),
            "active_students": sum(1 for report in reports if report["status"] == "active"),
            "completed_pretests": len(pre_scores),
            "completed_posttests": len(post_scores),
            "paired_pre_post": len(paired),
            "average_pretest_score": avg(pre_scores),
            "average_posttest_score": avg(post_scores),
            "average_absolute_improvement_points": avg(improvements),
            "reinforcement_cycles": sum(report["reinforcement"]["total"] for report in reports),
            "verified_reinforcement_cycles": sum(report["reinforcement"]["verified"] for report in reports),
            "escalated_reinforcement_cycles": sum(report["reinforcement"]["escalated"] for report in reports),
        },
        "students": reports,
        "reporting_notes": {
            "score_source": "Persisted completed assessment session scores; M07 does not recalculate placement.",
            "relative_improvement": "((post - pre) / pre) × 100; null when pretest score is 0 or either test is incomplete.",
            "speech_metrics": "Unavailable until calibrated speech evidence is accepted.",
        },
    }


@router.get("/summary")
def research_report_summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del user
    return build_cohort_research_report(db)


@router.get("/students/{student_id}")
def research_report_student(
    student_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del user
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")
    return build_student_research_report(db, student)
