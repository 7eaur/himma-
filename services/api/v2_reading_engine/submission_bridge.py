"""One bridge from V2 submitted reading audio to the native evidence queue.

No parallel legacy review decision is issued. The academic response is kept
pending in PostgreSQL until the provider's verified grade is applied in one
transaction. The student's browser never supplies a reference target.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.v2_reading_models import V2ReadingJob
from .pinned_reference import enqueue_pinned_reading


def create_reading_job(
    db: Session, *, student_id: int, audio_submission_id: int,
    content_release_id: int, question_id: str,
) -> int:
    """Attach only approved private pinned reading; caller commits atomically."""
    job = enqueue_pinned_reading(
        db, student_id=student_id,
        audio_submission_id=audio_submission_id,
        content_release_id=content_release_id, question_id=question_id,
    )
    return job.id


def pending_reading_job_id(
    db: Session, *, question_id: str, lesson_response_id: int | None = None,
    assessment_response_id: int | None = None,
) -> int | None:
    """Recover a current pending reading after refresh or lost HTTP response."""
    if (lesson_response_id is None) == (assessment_response_id is None):
        raise ValueError("Exactly one V2 answer owner is required")
    criteria = (
        V2ReadingJob.lesson_response_id == lesson_response_id
        if lesson_response_id is not None
        else V2ReadingJob.assessment_response_id == assessment_response_id
    )
    return db.scalar(
        select(V2ReadingJob.id).where(
            criteria, V2ReadingJob.question_id == question_id,
            V2ReadingJob.is_current.is_(True),
        )
    )
