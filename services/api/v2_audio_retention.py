"""P08 privacy: after review keep the latest finalized voice per child/question.

Never delete a pending or the only accepted recording. Deletion intent is
transactional; S3 deletion occurs AFTER commit and is retryable.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

import storage
from db.database import SessionLocal
from db.learning_models import (
    AssessmentQuestionResponse, LessonQuestionResponse, LessonSession,
)
from db.models import AudioPurgeTask, AudioSubmission, AssessmentSession

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
            task.storage_key = None
            task.status = "deleted"
            task.attempts += 1
            task.processed_at = datetime.now(timezone.utc)
            db.commit()
            processed += 1
    return {"deleted": processed, "deferred": failed}


def run_retention_after_commit() -> None:
    """Best-effort immediate cleanup; durable tasks survive process failures."""
    try:
        process_queued_audio_purges()
    except Exception:
        logger.exception("Deferred P08 retention worker, tasks stay in database")
