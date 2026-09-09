"""Canonical audio-review state helpers for learning runtime and adaptation.

This module is deliberately not a router and not a repair/overlay layer.  It is
the single shared policy helper for interpreting the *latest* audio submission
attached to each response while preserving earlier submissions as immutable
history.

Navigation and academic evidence are separate concerns:
- uploaded/pending is academically neutral and does not block same-level study;
- rerecord_required is a deferred learner task until the learner opens it;
- graded is the only review state that can become academic evidence;
- unresolved latest audio may hold promotion/level completion, but never turns
  into an automatic score.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from db.models import Attempt, AttemptResponse, AudioSubmission, AuditLog

PENDING_AUDIO_STATUSES = frozenset({"uploaded", "pending"})
UNRESOLVED_AUDIO_STATUSES = frozenset({"uploaded", "pending", "rerecord_required"})
RERECORD_OPEN_ACTION = "student.open_audio_rerecord"


@dataclass(frozen=True)
class AudioReviewSummary:
    pending_count: int = 0
    rerecord_required_count: int = 0

    @property
    def unresolved_count(self) -> int:
        return self.pending_count + self.rerecord_required_count

    @property
    def has_unresolved(self) -> bool:
        return self.unresolved_count > 0


def latest_audio_submission(
    db: Session,
    response: AttemptResponse | None,
) -> AudioSubmission | None:
    """Return only the newest submission for one response.

    Older invalid/reviewed submissions remain durable audit history and must not
    keep a response academically unresolved once a newer submission is graded.
    """
    if response is None:
        return None
    return (
        db.query(AudioSubmission)
        .filter(AudioSubmission.response_id == response.id)
        .order_by(AudioSubmission.id.desc())
        .first()
    )


def rerecord_task_is_open(
    db: Session,
    *,
    student_id: int,
    submission_id: int,
) -> bool:
    return db.query(AuditLog.id).filter(
        AuditLog.actor_role == "student",
        AuditLog.actor_id == student_id,
        AuditLog.action == RERECORD_OPEN_ACTION,
        AuditLog.entity_type == "AudioSubmission",
        AuditLog.entity_id == str(submission_id),
    ).first() is not None


def open_rerecord_task_once(
    db: Session,
    *,
    student_id: int,
    submission: AudioSubmission,
    details: str,
) -> bool:
    """Persist the learner's explicit decision to open a rerecord task once."""
    if rerecord_task_is_open(db, student_id=student_id, submission_id=submission.id):
        return False
    db.add(AuditLog(
        actor_role="student",
        actor_id=student_id,
        action=RERECORD_OPEN_ACTION,
        entity_type="AudioSubmission",
        entity_id=str(submission.id),
        details=details,
    ))
    return True


def session_audio_review_summary(db: Session, session_id: int) -> AudioReviewSummary:
    """Summarize unresolved *latest* submissions in one learning session."""
    responses = (
        db.query(AttemptResponse)
        .join(Attempt, Attempt.id == AttemptResponse.attempt_id)
        .filter(Attempt.session_id == session_id)
        .all()
    )
    pending = 0
    rerecord = 0
    for response in responses:
        submission = latest_audio_submission(db, response)
        if submission is None:
            continue
        if submission.status in PENDING_AUDIO_STATUSES:
            pending += 1
        elif submission.status == "rerecord_required":
            rerecord += 1
    return AudioReviewSummary(
        pending_count=pending,
        rerecord_required_count=rerecord,
    )
