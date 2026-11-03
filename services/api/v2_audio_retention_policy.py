"""Transactional V2 recording-retention policy, without S3 or deployment deps.

Both the historical reviewer and the native speech engine use exactly one
policy. Physical deletion is performed only by the post-commit maintenance job.
"""
from __future__ import annotations
from sqlalchemy.orm import Session
from db.learning_models import AssessmentQuestionResponse, LessonQuestionResponse, LessonSession
from db.models import AudioPurgeTask, AudioSubmission, AssessmentSession


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


