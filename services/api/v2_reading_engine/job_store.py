"""Transactional evidence queue for the native V2 reading engine.

The caller owns commit/rollback. No academic response or student progress is
changed here: P3 performs the single final atomic grade transition after
all dependent V2 routes have been replaced.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
import re

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from db.learning_models import (
    AssessmentQuestionResponse, LessonQuestionResponse, LessonSession,
)
from db.models import AssessmentSession, AudioSubmission
from db.v2_reading_models import V2ReadingEvaluation, V2ReadingJob
from v2_reading_engine.policy import ReadingDecision


POLICY_VERSION = "himma-v2-native-reading/1"
ALIAS_VERSION = "himma-v2-owner-approved-letter-aliases/1.2"
_RETRYABLE = frozenset({"retry_audio", "service_unavailable"})
_ERROR_CODE = re.compile(r"^[a-z][a-z0-9_]{0,99}$")


class ReadingConflict(ValueError):
    """A stale, unauthorized or conflicting operation must not change a grade."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _owner_context(db: Session, audio: AudioSubmission):
    if audio.lesson_response_id is not None:
        response = db.get(LessonQuestionResponse, audio.lesson_response_id)
        if response is None:
            raise ReadingConflict("Lesson response no longer exists")
        session = db.get(LessonSession, response.lesson_session_id)
        return ("lesson_response_id", response, session)
    if audio.assessment_response_id is not None:
        response = db.get(AssessmentQuestionResponse, audio.assessment_response_id)
        if response is None:
            raise ReadingConflict("Assessment response no longer exists")
        session = db.get(AssessmentSession, response.assessment_session_id)
        return ("assessment_response_id", response, session)
    raise ReadingConflict("Only V2 recording submissions may be evaluated")


def enqueue_reading(
    db: Session, *, student_id: int, audio_submission_id: int,
    content_release_id: int, question_id: str, reference_text: str,
    reading_kind: str, learning_mode: str,
) -> V2ReadingJob:
    """Create a job after validating recording, question, student and release.

    No uploads or provider calls here. The audio must already belong to a
    persisted V2 answer. New audio may supersede only a job that explicitly
    requested a re-recording or became unavailable.
    """
    if reading_kind not in {"letter", "word", "sentence", "text"}:
        raise ReadingConflict("Unrecognized reading task")
    if learning_mode not in {"training", "assessment"}:
        raise ReadingConflict("Unrecognized activity mode")
    if not question_id or not reference_text.strip():
        raise ReadingConflict("Pinned question and reference required")
    audio = db.get(AudioSubmission, audio_submission_id, with_for_update=True)
    if audio is None or not audio.storage_key.startswith(f"audio/{student_id}/"):
        raise ReadingConflict("Recording is not owned by this student")
    if audio.file_size <= 0:
        raise ReadingConflict("Recording has no usable content")
    owner_field, response, session = _owner_context(db, audio)
    if session is None or session.student_id != student_id:
        raise ReadingConflict("Session ownership mismatch")
    if session.content_release_id != content_release_id:
        raise ReadingConflict("Content snapshot mismatch")
    if response.question_id != question_id:
        raise ReadingConflict("Question mismatch")
    if owner_field == "assessment_response_id" and learning_mode != "assessment":
        raise ReadingConflict("Assessment recording must use assessment policy")

    checksum = sha256(reference_text.encode("utf-8")).hexdigest()
    existing = db.scalar(select(V2ReadingJob).where(
        V2ReadingJob.audio_submission_id == audio_submission_id))
    if existing:
        if (existing.student_id != student_id
                or existing.content_release_id != content_release_id
                or existing.question_id != question_id
                or existing.reference_sha256 != checksum
                or existing.reading_kind != reading_kind
                or existing.learning_mode != learning_mode):
            raise ReadingConflict("Recording submission is bound to another task")
        return existing

    current = db.scalar(select(V2ReadingJob).where(
        getattr(V2ReadingJob, owner_field) == response.id,
        V2ReadingJob.is_current.is_(True),
    ).with_for_update())
    if current:
        if current.status not in _RETRYABLE:
            raise ReadingConflict("Current reading still awaiting a final decision")
        current.is_current = False
        current.status = "superseded"
        current.lease_owner = None
        current.lease_expires_at = None
        current.version += 1
        current.updated_at = _now()
        db.flush()  # Release partial-unique current-row slot inside this transaction.

    job = V2ReadingJob(
        student_id=student_id, audio_submission_id=audio_submission_id,
        content_release_id=content_release_id, question_id=question_id,
        reference_text=reference_text, reference_sha256=checksum,
        reading_kind=reading_kind, learning_mode=learning_mode,
        policy_version=POLICY_VERSION, alias_catalog_version=ALIAS_VERSION,
        **{owner_field: response.id},
        status="queued", is_current=True,
    )
    db.add(job)
    db.flush()
    return job


def claim_reading(
    db: Session, *, worker_id: str, now: datetime | None = None,
    lease_seconds: int = 90,
) -> V2ReadingJob | None:
    """Claim one eligible job with SKIP LOCKED (PostgreSQL production).

    A crashed worker's expired lease can be reclaimed. A worker must present
    the *current* lease and version to record any decision.
    """
    if not worker_id or len(worker_id) > 160 or not 10 <= lease_seconds <= 900:
        raise ValueError("Invalid worker identity or lease duration")
    now = now or _now()
    candidate = db.scalar(
        select(V2ReadingJob).where(
            V2ReadingJob.is_current.is_(True),
            or_(
                V2ReadingJob.status == "queued",
                and_(V2ReadingJob.status == "retry_wait",
                     V2ReadingJob.next_attempt_at <= now),
                and_(V2ReadingJob.status == "processing",
                     V2ReadingJob.lease_expires_at <= now),
            ),
        ).order_by(V2ReadingJob.created_at, V2ReadingJob.id)
        .with_for_update(skip_locked=True).limit(1)
    )
    if candidate is None:
        return None
    candidate.updated_at = now
    candidate.version += 1
    if candidate.attempt_count >= candidate.max_attempts:
        candidate.status = "service_unavailable"
        candidate.lease_owner = None
        candidate.lease_expires_at = None
        candidate.last_error_code = "provider_attempts_exhausted"
        db.flush()
        return None
    candidate.attempt_count += 1
    candidate.status = "processing"
    candidate.lease_owner = worker_id
    candidate.lease_expires_at = now + timedelta(seconds=lease_seconds)
    candidate.next_attempt_at = None
    db.flush()
    return candidate


def _locked_worker_job(
    db: Session, *, job_id: int, worker_id: str,
    expected_version: int, now: datetime,
) -> V2ReadingJob:
    job = db.scalar(select(V2ReadingJob).where(
        V2ReadingJob.id == job_id).with_for_update())
    if (job is None or not job.is_current or job.status != "processing"
            or job.lease_owner != worker_id or job.version != expected_version
            or job.lease_expires_at is None or job.lease_expires_at <= now):
        raise ReadingConflict("Stale or unauthorized reading worker result")
    return job


def provider_failure(
    db: Session, *, job_id: int, worker_id: str, expected_version: int,
    error_code: str, now: datetime | None = None,
) -> V2ReadingJob:
    """Network/provider failure: retry same audio, never an academic zero."""
    if not _ERROR_CODE.fullmatch(error_code):
        raise ValueError("Error code must be sanitized and stable")
    now = now or _now()
    job = _locked_worker_job(db, job_id=job_id, worker_id=worker_id,
                             expected_version=expected_version, now=now)
    job.status = ("retry_wait" if job.attempt_count < job.max_attempts
                  else "service_unavailable")
    job.next_attempt_at = (
        now + timedelta(seconds=min(180, 5 * (2 ** (job.attempt_count - 1))))
        if job.status == "retry_wait" else None
    )
    job.lease_owner = None
    job.lease_expires_at = None
    job.last_error_code = error_code
    job.version += 1
    job.updated_at = now
    db.flush()
    return job


def record_evidence(
    db: Session, *, job_id: int, worker_id: str,
    expected_version: int, decision: ReadingDecision,
    provider_name: str, provider_request_id: str | None,
    transcript: str | None,
    now: datetime | None = None,
) -> V2ReadingEvaluation | None:
    """Record evidence exactly once, preserving decision provenance.

    Important: 'evidence_ready' is NOT an academic commit. P3 must make the
    response/skill/placement transition atomically with the final evaluation.
    """
    now = now or _now()
    job = _locked_worker_job(db, job_id=job_id, worker_id=worker_id,
                             expected_version=expected_version, now=now)
    if decision.reference != job.reference_text:
        raise ReadingConflict("Decision was derived from a different reference")
    if not provider_name or len(provider_name) > 100:
        raise ReadingConflict("Provider identity is required")
    if decision.status == "retry_audio":
        if decision.fraction is not None or decision.passed_for_progress is not None:
            raise ReadingConflict("Unrecognized speech must never have a grade")
        job.status = "retry_audio"
        evaluation = None
    elif decision.status in {"correct", "incorrect"}:
        frac = decision.fraction
        if (frac is None or not isinstance(frac, Decimal) or not frac.is_finite()
                or frac < 0 or frac > 1 or decision.passed_for_progress is None):
            raise ReadingConflict("Invalid or missing academic score")
        if (decision.status == "correct") != decision.passed_for_progress:
            raise ReadingConflict("Decision and academic pass are inconsistent")
        if db.scalar(select(V2ReadingEvaluation.id).where(
                V2ReadingEvaluation.job_id == job.id)) is not None:
            raise ReadingConflict("Reading evidence already recorded")
        evidence = {
            "provider": provider_name,
            "request_id": provider_request_id[:200] if provider_request_id else None,
            "transcript": transcript[:4000] if transcript else None,
            "reason": decision.reason,
            "reading_kind": job.reading_kind,
            "content_release_id": job.content_release_id,
            "question_id": job.question_id,
            "reference_checksum": job.reference_sha256,
            "policy_version": job.policy_version,
            "alias_catalog_version": job.alias_catalog_version,
            "matched_alias": decision.alias.matched_alias if decision.alias else None,
            "correct_words": decision.alignment.correct if decision.alignment else None,
            "deletions": decision.alignment.deletions if decision.alignment else None,
            "substitutions": decision.alignment.substitutions if decision.alignment else None,
            "insertions": decision.alignment.insertions if decision.alignment else None,
        }
        evaluation = V2ReadingEvaluation(
            job_id=job.id, audio_submission_id=job.audio_submission_id,
            decision=decision.status, score_fraction=frac,
            passed_for_progress=decision.passed_for_progress,
            evidence_json=evidence, decided_at=now,
        )
        db.add(evaluation)
        job.status = "evidence_ready"
    else:
        raise ReadingConflict("Unexpected evaluation state")
    job.lease_owner = None
    job.lease_expires_at = None
    job.next_attempt_at = None
    job.version += 1
    job.updated_at = now
    job.evaluated_at = now
    db.flush()
    return evaluation
