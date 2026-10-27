"""Durable asynchronous speech-analysis pipeline for P07."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import os

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from asr_governance import machine_review_decision
from db.models import AudioSubmission, AttemptResponse, ContentStep
from db.speech_models import SpeechAnalysis, SpeechAnalysisJob
from speech_alignment import align_reference, alignment_counts
from speech_provider import (
    ProviderNotConfigured,
    ProviderPermanentError,
    ProviderTemporaryError,
    SpeechProvider,
    build_provider,
)
import storage


RETRY_SECONDS = (30, 120, 600)
LEASE_SECONDS = int(os.getenv("HIMMA_ASR_JOB_LEASE_SECONDS", "600"))


def enqueue_submission(db: Session, submission_id: int) -> SpeechAnalysisJob:
    """Idempotently create one queue job per stored audio submission."""
    submission = db.query(AudioSubmission).filter(AudioSubmission.id == submission_id).first()
    if not submission:
        raise ValueError("Audio submission not found")

    existing = db.query(SpeechAnalysisJob).filter(
        SpeechAnalysisJob.submission_id == submission_id
    ).first()
    if existing:
        return existing

    job = SpeechAnalysisJob(submission_id=submission_id, status="queued")
    db.add(job)
    db.flush()
    return job


def _reference_for_submission(db: Session, submission: AudioSubmission) -> str:
    step = db.query(ContentStep).join(
        AttemptResponse, AttemptResponse.step_id == ContentStep.id
    ).filter(AttemptResponse.id == submission.response_id).first()
    if not step:
        raise ProviderPermanentError("Audio submission has no content step")
    reference = (step.expected_reading_text or step.prompt_text or "").strip()
    if not reference:
        raise ProviderPermanentError("Audio content has no reference reading text")
    return reference


def _audio_bytes(submission: AudioSubmission) -> bytes:
    try:
        response = storage.s3_client.get_object(
            Bucket=storage.S3_BUCKET_NAME,
            Key=submission.storage_key,
        )
        payload = response["Body"].read(storage.MAX_AUDIO_BYTES + 1)
    except Exception as exc:
        raise ProviderTemporaryError("Private audio storage is unavailable") from exc
    if not payload or len(payload) > storage.MAX_AUDIO_BYTES:
        raise ProviderPermanentError("Stored audio is empty or outside the allowed size")
    return payload


def _token_payload(aligned, provider_words):
    words = list(provider_words or ())
    payload = []
    for token in aligned:
        word = None
        if token.hypothesis_index is not None and token.hypothesis_index < len(words):
            word = words[token.hypothesis_index]
        payload.append({
            "kind": token.kind,
            "reference": token.reference,
            "hypothesis": token.hypothesis,
            "reference_index": token.reference_index,
            "hypothesis_index": token.hypothesis_index,
            "start_seconds": getattr(word, "start_seconds", None),
            "end_seconds": getattr(word, "end_seconds", None),
            "confidence": getattr(word, "confidence", None),
        })
    return payload


def _clear_lease(job: SpeechAnalysisJob) -> None:
    job.lease_owner = None
    job.lease_expires_at = None


def claim_next_job(
    db: Session,
    *,
    worker_id: str,
    now: datetime | None = None,
) -> SpeechAnalysisJob | None:
    """Atomically lease one due job using the database as queue authority.

    PostgreSQL workers use ``FOR UPDATE SKIP LOCKED`` so concurrent workers can
    never claim the same row. A crashed worker's ``processing`` row becomes
    claimable only after its persisted lease expires. The caller must commit the
    claim before performing the external provider call.
    """
    now = now or datetime.now(timezone.utc)
    if not worker_id.strip():
        raise ValueError("worker_id is required")
    due = or_(
        SpeechAnalysisJob.status == "queued",
        and_(
            SpeechAnalysisJob.status == "retry_wait",
            SpeechAnalysisJob.next_attempt_at <= now,
        ),
        and_(
            SpeechAnalysisJob.status == "processing",
            SpeechAnalysisJob.lease_expires_at.is_not(None),
            SpeechAnalysisJob.lease_expires_at <= now,
        ),
    )
    job = (
        db.query(SpeechAnalysisJob)
        .filter(due)
        .order_by(SpeechAnalysisJob.created_at, SpeechAnalysisJob.id)
        .with_for_update(skip_locked=True)
        .first()
    )
    if job is None:
        return None
    job.status = "processing"
    job.lease_owner = worker_id
    job.lease_expires_at = now + timedelta(seconds=LEASE_SECONDS)
    job.updated_at = now
    db.flush()
    return job


def process_job(
    db: Session,
    job_id: int,
    *,
    provider: SpeechProvider | None = None,
    now: datetime | None = None,
    worker_id: str | None = None,
) -> SpeechAnalysisJob:
    """Process exactly one job; safe to call repeatedly.

    Production workers pass ``worker_id`` after a committed durable lease. Direct
    calls without a worker id remain available to isolated tests/operator code,
    but the worker runtime never performs an unclaimed provider call.
    """
    now = now or datetime.now(timezone.utc)
    job = db.query(SpeechAnalysisJob).filter(SpeechAnalysisJob.id == job_id).first()
    if not job:
        raise ValueError("Speech analysis job not found")
    if job.status in {"completed", "review_required", "failed", "dead_letter"}:
        return job
    if worker_id is not None:
        if (
            job.status != "processing"
            or job.lease_owner != worker_id
            or job.lease_expires_at is None
            or job.lease_expires_at <= now
        ):
            raise RuntimeError("Speech analysis job is not leased by this worker")
    elif job.status == "retry_wait" and job.next_attempt_at and job.next_attempt_at > now:
        return job

    existing = db.query(SpeechAnalysis).filter(SpeechAnalysis.job_id == job.id).first()
    if existing:
        job.status = "completed" if existing.decision == "auto_accepted" else "review_required"
        job.completed_at = job.completed_at or now
        job.updated_at = now
        _clear_lease(job)
        db.flush()
        return job

    submission = db.query(AudioSubmission).filter(AudioSubmission.id == job.submission_id).first()
    if not submission:
        job.status = "failed"
        job.last_error_code = "submission_missing"
        job.last_error_message = "Audio submission not found"
        job.updated_at = now
        _clear_lease(job)
        db.flush()
        return job

    if worker_id is None:
        job.status = "processing"
        job.updated_at = now
        db.flush()

    try:
        reference = _reference_for_submission(db, submission)
        payload = _audio_bytes(submission)
        runtime_provider = provider or build_provider()
        result = runtime_provider.transcribe_reference_guided(
            audio_bytes=payload,
            mime_type=submission.mime_type,
            reference_text=reference,
            language="ar",
        )
        aligned = align_reference(reference, result.transcript)
        counts = alignment_counts(aligned)
        decision, calibration_version = machine_review_decision(
            provider_name=result.provider_name,
            model=result.model,
            confidence=result.confidence,
        )
        analysis = SpeechAnalysis(
            job_id=job.id,
            submission_id=submission.id,
            provider_name=result.provider_name,
            provider_model=result.model,
            provider_request_id=result.request_id,
            reference_text=reference,
            transcript_text=result.transcript,
            overall_confidence=(Decimal(str(result.confidence)) if result.confidence is not None else None),
            decision=decision,
            correct_count=counts["correct"],
            deletion_count=counts["deletion"],
            insertion_count=counts["insertion"],
            substitution_count=counts["substitution"],
            duration_seconds=(Decimal(str(result.duration_seconds)) if result.duration_seconds is not None else None),
            tokens_json=_token_payload(aligned, result.words),
            provider_payload=result.raw_metadata or None,
            calibration_version=calibration_version,
        )
        db.add(analysis)
        job.attempt_count += 1
        job.status = "completed" if decision == "auto_accepted" else "review_required"
        job.last_error_code = None
        job.last_error_message = None
        job.next_attempt_at = None
        job.completed_at = now
        job.updated_at = now
        _clear_lease(job)
        db.flush()
        return job
    except ProviderNotConfigured as exc:
        job.status = "blocked_provider"
        job.last_error_code = "provider_not_configured"
        job.last_error_message = str(exc)
        job.next_attempt_at = None
        job.updated_at = now
        _clear_lease(job)
        db.flush()
        return job
    except ProviderTemporaryError as exc:
        job.attempt_count += 1
        job.last_error_code = "temporary_provider_error"
        job.last_error_message = str(exc)
        if job.attempt_count >= job.max_attempts:
            job.status = "dead_letter"
            job.next_attempt_at = None
        else:
            delay = RETRY_SECONDS[min(job.attempt_count - 1, len(RETRY_SECONDS) - 1)]
            job.status = "retry_wait"
            job.next_attempt_at = now + timedelta(seconds=delay)
        job.updated_at = now
        _clear_lease(job)
        db.flush()
        return job
    except ProviderPermanentError as exc:
        job.attempt_count += 1
        job.status = "failed"
        job.last_error_code = "permanent_analysis_error"
        job.last_error_message = str(exc)
        job.next_attempt_at = None
        job.updated_at = now
        _clear_lease(job)
        db.flush()
        return job


def claimable_job_ids(db: Session, *, now: datetime | None = None, limit: int = 10) -> list[int]:
    """Read-only diagnostics; production workers use ``claim_next_job``."""
    now = now or datetime.now(timezone.utc)
    rows = db.query(SpeechAnalysisJob.id).filter(
        or_(
            SpeechAnalysisJob.status == "queued",
            and_(SpeechAnalysisJob.status == "retry_wait", SpeechAnalysisJob.next_attempt_at <= now),
            and_(
                SpeechAnalysisJob.status == "processing",
                SpeechAnalysisJob.lease_expires_at.is_not(None),
                SpeechAnalysisJob.lease_expires_at <= now,
            ),
        )
    ).order_by(SpeechAnalysisJob.created_at, SpeechAnalysisJob.id).limit(limit).all()
    return [row.id for row in rows]
