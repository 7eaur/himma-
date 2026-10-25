"""P08 privacy: after review keep the latest finalized voice per child/question.

Never delete a pending or the only accepted recording. Deletion intent is
transactional; S3 deletion occurs AFTER commit and is retryable.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

import storage
from db.database import SessionLocal
from db.learning_models import (
    AssessmentQuestionResponse, LessonQuestionResponse, LessonSession,
)
from db.models import AudioPurgeTask, AudioSubmission, AudioUploadLease, AssessmentSession

logger = logging.getLogger(__name__)


def _enqueue(db: Session, student_id: int, key: str) -> None:
    if not key.startswith(f"audio/{student_id}/"):
        raise ValueError("Attempted to purge audio with invalid student ownership")
    existing = db.query(AudioPurgeTask).filter(AudioPurgeTask.storage_key == key).one_or_none()
    if existing is None:
        db.add(AudioPurgeTask(student_id=student_id, storage_key=key, status="queued"))
        db.flush()  # Deduplicate keys even when the Session disables autoflush.


def schedule_superseded_audio(
    db: Session, *, student_id: int, question_id: str,
    winning_audio_id: int, kind: str, extra_staged_keys: tuple[str, ...] = (),
) -> None:
    """Queue only old material belonging to this student's SAME question.

    Called inside the human-review transaction after new audio was verified.
    Repeated review calls cannot queue a winning or pending recording.
    """
    if kind == "lesson":
        older = (
            db.query(AudioSubmission)
            .join(LessonQuestionResponse, AudioSubmission.lesson_response_id == LessonQuestionResponse.id)
            .join(LessonSession, LessonQuestionResponse.lesson_session_id == LessonSession.id)
            .filter(LessonSession.student_id == student_id, LessonQuestionResponse.question_id == question_id)
        )
    elif kind in ("pretest", "posttest"):
        older = (
            db.query(AudioSubmission)
            .join(AssessmentQuestionResponse, AudioSubmission.assessment_response_id == AssessmentQuestionResponse.id)
            .join(AssessmentSession, AssessmentQuestionResponse.assessment_session_id == AssessmentSession.id)
            .filter(AssessmentSession.student_id == student_id, AssessmentQuestionResponse.question_id == question_id)
        )
    else:
        raise ValueError("Unknown V2 audio context")

    rows = older.order_by(AudioSubmission.id.desc()).all()
    accepted = [row for row in rows if row.status == "graded"]
    if not accepted or all(row.id != winning_audio_id for row in accepted):
        raise ValueError("Cannot prune audio without an accepted winning take")
    # The latest REVIEWED recorded take wins. A later review of an old take
    # cannot delete an already finalized, newer recording.
    latest = max(accepted, key=lambda row: row.id)
    for row in rows:
        if row.id == latest.id or row.status not in ("graded", "rerecord_required", "retention_pending"):
            continue
        _enqueue(db, student_id, row.storage_key)
        row.status = "retention_pending"
    for key in extra_staged_keys:
        if key != latest.storage_key:
            _enqueue(db, student_id, key)


def schedule_superseded_staged_audio(db: Session, *, student_id: int, keys: tuple[str, ...]) -> None:
    """Old unsubmitted re-recordings can be purged after the next take is staged."""
    for key in keys:
        _enqueue(db, student_id, key)


def process_queued_audio_purges(limit: int = 30) -> dict[str, int]:
    """Idempotent maintenance. All records stay queued if S3 is unavailable.

    Do not return storage keys, or let a failed storage delete alter a grade.
    A worker/cron can call this again after an interrupted API process.
    """
    processed = 0
    failed = 0
    with SessionLocal() as db:
        pending = db.query(AudioPurgeTask).filter(
            AudioPurgeTask.status == "queued",
        ).order_by(AudioPurgeTask.id).limit(limit).all()
        for task in pending:
            key = task.storage_key
            if not key:
                continue
            db.refresh(task, with_for_update=True)
            if task.status != "queued":
                continue
            if not key.startswith(f"audio/{task.student_id}/"):
                logger.error("Invalid V2 audio deletion task id=%s", task.id)
                failed += 1
                continue
            linked = db.query(AudioSubmission).filter(AudioSubmission.storage_key == key).all()
            if any(row.status != "retention_pending" for row in linked):
                logger.warning("V2 audio deletion blocked by live evidence: task=%s", task.id)
                failed += 1
                continue
            try:
                storage.delete_superseded_audio(key, task.student_id)
            except (RuntimeError, ValueError):
                db.rollback()
                logger.warning("V2 audio cleanup deferred task=%s", task.id)
                failed += 1
                continue
            for row in linked:
                row.storage_key = f"purged/{row.id}"
                row.status = "purged"
            for lease in db.query(AudioUploadLease).filter(AudioUploadLease.storage_key == key).all():
                lease.storage_key = None
                lease.state = "purged"
            task.storage_key = None
            task.status = "deleted"
            task.attempts += 1
            task.processed_at = datetime.now(timezone.utc)
            db.commit()
            processed += 1
    return {"deleted": processed, "deferred": failed}


def track_new_audio_upload(db: Session, *, student_id: int, storage_key: str) -> None:
    """Register S3 content as unsubmitted until an answer transaction accepts it."""
    if not storage_key.startswith(f"audio/{student_id}/"):
        raise ValueError("Audio upload student mismatch")
    lease = db.query(AudioUploadLease).filter(AudioUploadLease.storage_key == storage_key).one_or_none()
    if lease is not None:
        if lease.student_id != student_id or lease.state not in ("temporary", "submitted"):
            raise ValueError("Audio upload no longer available or owned by another student")
        return
    db.add(AudioUploadLease(student_id=student_id, storage_key=storage_key, state="temporary"))
    db.flush()


def mark_audio_submitted(db: Session, *, student_id: int, storage_key: str) -> None:
    """Serialize submission with the orphan sweeper on the same upload lease.

    Legacy pre-lease uploads still work with owner validation in _canonical_answer.
    """
    lease = db.query(AudioUploadLease).filter(AudioUploadLease.storage_key == storage_key).with_for_update().one_or_none()
    if lease is None:
        return
    if lease.student_id != student_id or lease.state not in ("temporary", "submitted"):
        raise ValueError("This audio upload is no longer available")
    lease.state = "submitted"
    lease.submitted_at = datetime.now(timezone.utc)


def process_abandoned_uploads(*, age_hours: int = 24, limit: int = 30) -> dict[str, int]:
    """Delete only unsubmitted leases older than a recovery grace period."""
    if age_hours < 24:
        raise ValueError("The abandoned upload grace period must be at least 24 hours")
    removed = 0
    deferred = 0
    cutoff = datetime.now(timezone.utc) - timedelta(hours=age_hours)
    with SessionLocal() as db:
        leases = db.query(AudioUploadLease).filter(
            AudioUploadLease.state == "temporary",
            AudioUploadLease.created_at < cutoff,
        ).order_by(AudioUploadLease.id).limit(limit).all()
        for candidate in leases:
            lease = db.query(AudioUploadLease).filter(
                AudioUploadLease.id == candidate.id,
                AudioUploadLease.state == "temporary",
            ).with_for_update().one_or_none()
            if lease is None or not lease.storage_key:
                continue
            key = lease.storage_key
            if (not key.startswith(f"audio/{lease.student_id}/") or
                    db.query(AudioSubmission).filter(AudioSubmission.storage_key == key).first() is not None or
                    db.query(AudioPurgeTask).filter(AudioPurgeTask.storage_key == key).first() is not None):
                deferred += 1
                db.rollback()
                continue
            try:
                storage.delete_superseded_audio(key, lease.student_id)
            except (RuntimeError, ValueError):
                db.rollback()
                deferred += 1
                continue
            lease.storage_key = None
            lease.state = "purged"
            db.commit()
            removed += 1
    return {"deleted_abandoned": removed, "deferred_abandoned": deferred}


def run_audio_maintenance() -> dict[str, int]:
    """Both queues are bounded, safe to retry, and independent of grading."""
    return {**process_queued_audio_purges(), **process_abandoned_uploads()}


def run_retention_after_commit() -> None:
    """Best-effort immediate cleanup; durable tasks survive process failures."""
    try:
        run_audio_maintenance()
    except Exception:
        logger.exception("Deferred P08 retention worker, tasks stay in database")
