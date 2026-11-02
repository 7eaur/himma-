"""P08 privacy: after review keep the latest finalized voice per child/question.

Never delete a pending or the only accepted recording. Deletion intent is
transactional; S3 deletion occurs AFTER commit and is retryable.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from v2_audio_leases import audio_upload_binding, track_new_audio_upload, mark_audio_submitted
from v2_audio_retention_policy import schedule_superseded_audio, schedule_superseded_staged_audio

import storage
from db.database import SessionLocal
from db.learning_models import (
    AssessmentQuestionResponse, LessonQuestionResponse, LessonSession,
)
from db.models import AudioPurgeTask, AudioSubmission, AudioUploadLease, AssessmentSession

logger = logging.getLogger(__name__)


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
