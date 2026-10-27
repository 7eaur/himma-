"""Reviewed V2 child-reading archive: private, latest accepted recording per item.

Read-only supervisor view. No AI results are fabricated. Media links remain
on the existing session-scoped, supervisor-authorized streaming endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, literal, select, union_all
from sqlalchemy.orm import Session

from db.learning_models import (
    AssessmentQuestionResponse, LessonQuestionResponse, LessonSession, V2AudioRubric,
)
from db.models import AssessmentSession, AudioSubmission, Student, User
from dependencies import get_current_user, get_db

router = APIRouter(prefix="/v2/review", tags=["v2-reviewed-audio"])


@router.get("/reviewed-recordings")
def reviewed_recordings(
    student_id: int | None = Query(default=None, ge=1),
    kind: str = Query(default="all", pattern="^(all|lesson|pretest|posttest)$"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _supervisor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Only graded audio appears; pending and replaced takes are not exposed."""
    lesson = (
        select(
            AudioSubmission.id.label("audio_id"),
            LessonQuestionResponse.id.label("response_id"),
            LessonSession.student_id.label("student_id"),
            LessonQuestionResponse.question_id.label("question_id"),
            LessonSession.lesson_id.label("context_id"),
            literal("lesson").label("kind"),
            LessonQuestionResponse.is_correct.label("is_correct"),
            LessonQuestionResponse.reviewed_at.label("reviewed_at"),
            AudioSubmission.submitted_at.label("submitted_at"),
            AudioSubmission.duration_seconds.label("duration_seconds"),
        )
        .join(LessonQuestionResponse, AudioSubmission.lesson_response_id == LessonQuestionResponse.id)
        .join(LessonSession, LessonQuestionResponse.lesson_session_id == LessonSession.id)
        .where(
            AudioSubmission.status == "graded",
            LessonQuestionResponse.status == "graded",
            LessonQuestionResponse.reviewed_at.is_not(None),
        )
    )
    assessment = (
        select(
            AudioSubmission.id.label("audio_id"),
            AssessmentQuestionResponse.id.label("response_id"),
            AssessmentSession.student_id.label("student_id"),
            AssessmentQuestionResponse.question_id.label("question_id"),
            literal(None).label("context_id"),
            AssessmentSession.session_type.label("kind"),
            AssessmentQuestionResponse.is_correct.label("is_correct"),
            AssessmentQuestionResponse.reviewed_at.label("reviewed_at"),
            AudioSubmission.submitted_at.label("submitted_at"),
            AudioSubmission.duration_seconds.label("duration_seconds"),
        )
        .join(AssessmentQuestionResponse, AudioSubmission.assessment_response_id == AssessmentQuestionResponse.id)
        .join(AssessmentSession, AssessmentQuestionResponse.assessment_session_id == AssessmentSession.id)
        .where(
            AudioSubmission.status == "graded",
            AssessmentQuestionResponse.status == "graded",
            AssessmentQuestionResponse.reviewed_at.is_not(None),
            AssessmentSession.session_type.in_(("pretest", "posttest")),
        )
    )
    if kind == "lesson":
        sources = lesson.subquery("recording_sources")
    elif kind in {"pretest", "posttest"}:
        sources = assessment.where(AssessmentSession.session_type == kind).subquery("recording_sources")
    else:
        sources = union_all(lesson, assessment).subquery("recording_sources")

    newest = (
        select(
            *[sources.c[key] for key in (
                "audio_id", "response_id", "student_id", "question_id",
                "context_id", "kind", "is_correct", "reviewed_at",
                "submitted_at", "duration_seconds",
            )],
            func.row_number().over(
                partition_by=(sources.c.student_id, sources.c.question_id),
                order_by=(sources.c.submitted_at.desc(), sources.c.audio_id.desc()),
            ).label("latest_rank"),
        )
        .where(sources.c.student_id == student_id if student_id else literal(True))
    ).subquery("ranked_recordings")
    ordered = (
        select(newest).where(newest.c.latest_rank == 1)
        .order_by(newest.c.reviewed_at.desc(), newest.c.audio_id.desc())
        .offset(offset).limit(limit + 1)
    )
    rows = db.execute(ordered).mappings().all()
    ids = {int(row["student_id"]) for row in rows[:limit]}
    names = {student.id: student.name for student in db.query(Student).filter(Student.id.in_(ids)).all()} if ids else {}
    audio_ids = [int(row["audio_id"]) for row in rows[:limit]]
    # Load all V2-only human rubrics in one query, never by asking the legacy
    # V1 AudioReview ledger or leaking an unapproved score.
    rubric_by_audio = {
        record.audio_submission_id: record
        for record in db.query(V2AudioRubric).filter(
            V2AudioRubric.audio_submission_id.in_(audio_ids),
        ).all()
    } if audio_ids else {}
    items = []
    for row in rows[:limit]:
        if row["kind"] == "lesson":
            url = f"/api/v2/review/lessons/{row['response_id']}/audio"
        else:
            url = f"/api/v2/assessments/admin/responses/{row['response_id']}/audio"
        rubric = rubric_by_audio.get(row["audio_id"])
        items.append({
            "audio_id": row["audio_id"],
            "reading_rubric": {
                "target_units": rubric.target_units,
                "deletions": rubric.deletions,
                "substitutions": rubric.substitutions,
                "insertions": rubric.insertions,
                "rubric_percent": round(float(rubric.rubric_score) * 100, 1),
                "is_correct": rubric.is_correct,
                "pronunciation_notes": rubric.pronunciation_notes,
                "fluency_notes": rubric.fluency_notes,
                "policy_version": rubric.policy_version,
            } if rubric is not None else None,
            "response_id": row["response_id"],
            "student_id": row["student_id"],
            "student_name": names.get(row["student_id"], "طالب"),
            "question_id": row["question_id"],
            "lesson_id": row["context_id"],
            "kind": row["kind"],
            "is_correct": row["is_correct"],
            "evaluation_source": "supervisor",
            "reviewed_at": row["reviewed_at"].isoformat() if row["reviewed_at"] else None,
            "duration_seconds": float(row["duration_seconds"]) if row["duration_seconds"] is not None else None,
            "audio_url": url,
        })
    return {
        "items": items,
        "next_offset": offset + limit if len(rows) > limit else None,
        "evaluation_sources": ["supervisor"],
    }
