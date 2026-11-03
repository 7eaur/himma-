"""Atomic application of a verified reading evaluation.

This is a transaction component, not a public API or background startup hook.
The caller MUST provide the academic continuation that advances the correct
student session / support policy in the *same* database transaction; if that
continuation fails everything is rolled back by the caller.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.learning_models import (
    AssessmentQuestionResponse, LessonQuestionResponse, LessonSession,
    SkillEvidence,
)
from db.models import AssessmentSession, AudioSubmission, AuditLog
from db.v2_reading_models import V2ReadingEvaluation, V2ReadingJob
from .job_store import ReadingConflict
from v2_audio_retention_policy import schedule_superseded_audio


def apply_evaluation(
    db: Session,
    *,
    job_id: int,
    continue_academic_journey: Callable[[Session, object, object], None],
) -> bool:
    """Apply once to V2 answer/skill and invoke the journey reconciler.

    Returns False for an exact replay after a successful academic commit.
    Never commits itself. The caller's transaction wraps all changes.
    """
    job = db.scalar(select(V2ReadingJob).where(
        V2ReadingJob.id == job_id).with_for_update())
    if job is None or not job.is_current:
        raise ReadingConflict("Reading job is not current")
    if job.status == "applied":
        return False
    if job.status != "evidence_ready":
        raise ReadingConflict("Unresolved reading evidence cannot change grades")
    result = db.scalar(select(V2ReadingEvaluation).where(
        V2ReadingEvaluation.job_id == job.id).with_for_update())
    audio = db.scalar(select(AudioSubmission).where(
        AudioSubmission.id == job.audio_submission_id).with_for_update())
    if (result is None or audio is None
            or result.audio_submission_id != job.audio_submission_id
            or not audio.storage_key.startswith(f"audio/{job.student_id}/")):
        raise ReadingConflict("Reading evidence or private audio ownership mismatch")
    if not isinstance(result.score_fraction, Decimal):
        result_fraction = Decimal(str(result.score_fraction))
    else:
        result_fraction = result.score_fraction
    if (not result_fraction.is_finite() or result_fraction < 0 or result_fraction > 1
            or (result.decision == "correct") != result.passed_for_progress):
        raise ReadingConflict("Reading score and decision are inconsistent")

    if job.assessment_response_id is not None:
        if audio.assessment_response_id != job.assessment_response_id:
            raise ReadingConflict("Assessment recording binding mismatch")
        response = db.scalar(select(AssessmentQuestionResponse).where(
            AssessmentQuestionResponse.id == job.assessment_response_id
        ).with_for_update())
        if response is None:
            raise ReadingConflict("Assessment answer missing")
        session = db.scalar(select(AssessmentSession).where(
            AssessmentSession.id == response.assessment_session_id
        ).with_for_update())
        if job.learning_mode != "assessment":
            raise ReadingConflict("Assessment must use assessment mode")
        proof = None
    elif job.lesson_response_id is not None:
        if audio.lesson_response_id != job.lesson_response_id:
            raise ReadingConflict("Lesson recording binding mismatch")
        response = db.scalar(select(LessonQuestionResponse).where(
            LessonQuestionResponse.id == job.lesson_response_id
        ).with_for_update())
        if response is None:
            raise ReadingConflict("Lesson answer missing")
        session = db.scalar(select(LessonSession).where(
            LessonSession.id == response.lesson_session_id
        ).with_for_update())
        proof = db.scalar(select(SkillEvidence).where(
            SkillEvidence.response_id == response.id).with_for_update())
        if proof is None or proof.review_status != "pending_review":
            raise ReadingConflict("Reading skill evidence missing or already finalized")
        if (proof.lesson_session_id != session.id or proof.student_id != job.student_id
                or proof.question_id != job.question_id):
            raise ReadingConflict("Skill evidence binding mismatch")
    else:
        raise ReadingConflict("No V2 answer bound to reading job")

    if (session is None or session.student_id != job.student_id
            or session.content_release_id != job.content_release_id
            or response.question_id != job.question_id
            or response.status != "pending_review"
            or response.is_correct is not None
            or response.question_score_fraction is not None):
        raise ReadingConflict("Academic session or answer has changed since analysis")

    timestamp = datetime.now(timezone.utc)
    response.status = "graded"
    response.is_correct = result.passed_for_progress
    response.question_score_fraction = result_fraction
    response.reviewed_at = timestamp
    audio.status = "graded"
    if proof is not None:
        proof.review_status = "graded"
        proof.is_correct = result.passed_for_progress
        proof.reviewed_at = timestamp
        proof.counts_for_mastery = proof.role in {"independent_check", "support_check"}

    job.status = "applied"
    job.updated_at = timestamp
    job.version += 1

    db.add(AuditLog(
        actor_role="system", actor_id=0, action="v2_reading_auto_graded",
        entity_type="reading_job", entity_id=str(job.id),
        details=(f"policy={job.policy_version};audio_id={audio.id};"
                 f"score={result_fraction};passed={result.passed_for_progress}"),
    ))
    db.flush()

    # Mandatory: continue lesson/support or assessment/placement atomically.
    # Any exception forces the caller to roll back this entire transaction.
    continue_academic_journey(db, response, session)
    # Schedule privacy cleanup in the SAME academic transaction. The purge
    # worker deletes bytes only after commit and never deletes a pending take.
    schedule_superseded_audio(
        db, student_id=job.student_id, question_id=job.question_id,
        winning_audio_id=audio.id,
        kind=("lesson" if job.lesson_response_id is not None
              else session.session_type),
    )
    db.flush()
    return True
