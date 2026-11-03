"""Native V2 unclear-audio retry: replace the take, NOT the academic answer.

A student can submit another recording only after the provider returned
retry_audio (not after incorrect pronunciation or a transient service error).
The original V2 answer and the teacher-independent attempt count remain fixed.
This module never commits and never directly calls S3/Azure.
"""
from __future__ import annotations

from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.learning_models import AssessmentQuestionResponse, LessonQuestionResponse
from db.models import AudioSubmission
from db.v2_reading_models import V2ReadingJob
from v2_audio_leases import audio_upload_binding, mark_audio_submitted

from .job_store import ReadingConflict
from .pinned_reference import enqueue_pinned_reading


def _owner(db: Session, job: V2ReadingJob) -> AssessmentQuestionResponse | LessonQuestionResponse:
    if job.assessment_response_id is not None:
        response = db.get(AssessmentQuestionResponse, job.assessment_response_id)
    elif job.lesson_response_id is not None:
        response = db.get(LessonQuestionResponse, job.lesson_response_id)
    else:
        response = None
    if (response is None or response.question_id != job.question_id
            or response.status != "pending_review" or response.is_correct is not None
            or response.question_score_fraction is not None):
        raise ReadingConflict("Reading answer is no longer eligible for re-recording")
    return response


def _matching_audio(db: Session, job: V2ReadingJob, storage_key: str) -> AudioSubmission | None:
    owner_column = (
        AudioSubmission.assessment_response_id if job.assessment_response_id is not None
        else AudioSubmission.lesson_response_id
    )
    response_id = job.assessment_response_id or job.lesson_response_id
    return db.scalar(select(AudioSubmission).where(
        owner_column == response_id,
        AudioSubmission.storage_key == storage_key,
    ))


def retry_is_allowed(db: Session, *, student_id: int, job_id: int) -> V2ReadingJob:
    """Validate ownership/status before accepting any new private upload."""
    job = db.scalar(select(V2ReadingJob).where(
        V2ReadingJob.id == job_id,
        V2ReadingJob.student_id == student_id,
        V2ReadingJob.is_current.is_(True),
        V2ReadingJob.status == "retry_audio",
    ).with_for_update())
    if job is None:
        raise ReadingConflict("Recording cannot be replaced in its current state")
    _owner(db, job)
    return job


def attach_retry_take(
    db: Session, *, student_id: int, job_id: int,
    storage_key: str, file_size: int, mime_type: str,
    duration_seconds: float,
) -> V2ReadingJob:
    """Bind a staged audio lease, supersede the old job and create a new job.

    Retries with the same storage key are idempotent; other recordings cannot
    replace an already-enqueued re-recording, even across worker crashes.
    """
    if (not storage_key.startswith(f"audio/{student_id}/") or
            file_size <= 0 or file_size > 10 * 1024 * 1024 or
            not mime_type.startswith("audio/") or
            not 0 < duration_seconds <= 900):
        raise ReadingConflict("Retry recording metadata is invalid")

    original = db.scalar(select(V2ReadingJob).where(
        V2ReadingJob.id == job_id,
        V2ReadingJob.student_id == student_id,
    ).with_for_update())
    if original is None:
        raise ReadingConflict("Reading job is unavailable")
    existing_audio = _matching_audio(db, original, storage_key)
    if existing_audio is not None:
        if existing_audio.id == original.audio_submission_id:
            raise ReadingConflict("Original unclear audio cannot be reused as a retry")
        existing_job = db.scalar(select(V2ReadingJob).where(
            V2ReadingJob.audio_submission_id == existing_audio.id,
            V2ReadingJob.is_current.is_(True),
        ))
        if (existing_job is None or existing_job.student_id != student_id
                or existing_audio.file_size != file_size
                or existing_audio.mime_type != mime_type):
            raise ReadingConflict("Audio retry cannot be replayed with different evidence")
        return existing_job

    if not original.is_current or original.status != "retry_audio":
        raise ReadingConflict("Only unclear speech may be re-recorded")
    _owner(db, original)

    binding = audio_upload_binding("retry", original.id, original.question_id)
    mark_audio_submitted(
        db, student_id=student_id, storage_key=storage_key, binding_key=binding,
    )
    audio = AudioSubmission(
        response_id=None,
        lesson_response_id=original.lesson_response_id,
        assessment_response_id=original.assessment_response_id,
        storage_key=storage_key, file_size=file_size, mime_type=mime_type,
        duration_seconds=Decimal(str(duration_seconds)),
        status="pending_review",
    )
    db.add(audio)
    db.flush()

    job = enqueue_pinned_reading(
        db, student_id=student_id, audio_submission_id=audio.id,
        content_release_id=original.content_release_id,
        question_id=original.question_id,
    )
    if (job.id == original.id or job.reference_sha256 != original.reference_sha256
            or job.learning_mode != original.learning_mode):
        raise ReadingConflict("The original pinned reading policy has changed")
    previous_audio = db.get(AudioSubmission, original.audio_submission_id, with_for_update=True)
    if previous_audio is None or previous_audio.status not in ("pending_review", "rerecord_required"):
        raise ReadingConflict("Previous audio cannot safely be superseded")
    # Preserve bytes until the new take is conclusively graded; only then
    # schedule the old recording for post-commit deletion.
    previous_audio.status = "rerecord_required"
    db.flush()
    return job
