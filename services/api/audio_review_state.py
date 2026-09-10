"""Canonical audio-review state helpers for assessment, learning and adaptation.

This module is deliberately not a router and not a repair/overlay layer. It is
the shared policy owner for interpreting the *latest* audio submission attached
to each response while preserving every older submission as immutable history.

Navigation and academic evidence are separate concerns:
- uploaded/pending is academically neutral;
- learning may continue inside the same level while audio is unresolved;
- assessment may still choose to hold item advancement until review resolves;
- rerecord_required is deferred until the learner explicitly opens the task;
- graded is the only review state that can become academic evidence;
- historical submissions never override the state of a newer submission.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from db.models import Attempt, AttemptResponse, AudioReview, AudioSubmission, AuditLog

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
    """Return only the newest submission for one response."""
    if response is None:
        return None
    return (
        db.query(AudioSubmission)
        .filter(AudioSubmission.response_id == response.id)
        .order_by(AudioSubmission.id.desc())
        .first()
    )


def latest_audio_review(
    db: Session,
    submission: AudioSubmission | None,
) -> AudioReview | None:
    """Return the newest manual review for one immutable submission."""
    if submission is None:
        return None
    return (
        db.query(AudioReview)
        .filter(AudioReview.submission_id == submission.id)
        .order_by(AudioReview.id.desc())
        .first()
    )


def session_latest_audio_submissions(
    db: Session,
    session_id: int,
) -> list[tuple[AttemptResponse, AudioSubmission]]:
    """Return each response's latest submission for one session.

    A rerecord creates another AudioSubmission for the same AttemptResponse. This
    function deliberately collapses only for *state interpretation*; it never
    deletes or rewrites the historical rows.
    """
    responses = (
        db.query(AttemptResponse)
        .join(Attempt, Attempt.id == AttemptResponse.attempt_id)
        .filter(Attempt.session_id == session_id)
        .all()
    )
    result: list[tuple[AttemptResponse, AudioSubmission]] = []
    for response in responses:
        submission = latest_audio_submission(db, response)
        if submission is not None:
            result.append((response, submission))
    return result


def session_attempt_ids_with_latest_audio_status(
    db: Session,
    session_id: int,
    statuses: set[str] | frozenset[str],
) -> set[int]:
    """Return attempt ids whose response has a latest submission in ``statuses``."""
    wanted = set(statuses)
    if not wanted:
        return set()
    return {
        int(response.attempt_id)
        for response, submission in session_latest_audio_submissions(db, session_id)
        if submission.status in wanted
    }


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
    """Summarize unresolved *latest* submissions in one session."""
    pending = 0
    rerecord = 0
    for _, submission in session_latest_audio_submissions(db, session_id):
        if submission.status in PENDING_AUDIO_STATUSES:
            pending += 1
        elif submission.status == "rerecord_required":
            rerecord += 1
    return AudioReviewSummary(
        pending_count=pending,
        rerecord_required_count=rerecord,
    )
