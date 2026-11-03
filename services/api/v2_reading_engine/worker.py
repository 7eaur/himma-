"""One asynchronous native V2 reading-job execution.

The caller starts this loop within the EXISTING Himma API process only after
full release cutover. This module deliberately has no automatic startup hook.
A claimed job is committed before contacting Azure, and the evaluated evidence
is committed after validating the lease/version and current audio owner.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session
from db.v2_reading_models import V2ReadingJob

from db.models import AudioSubmission
from v2_reading_engine.azure_provider import AzureSpeechProvider, SpeechEvidence
from v2_reading_engine.job_store import (
    ReadingConflict, claim_reading, provider_failure, record_evidence,
)
from v2_reading_engine.policy import evaluate_reading


@dataclass(frozen=True)
class WorkItem:
    id: int
    version: int
    student_id: int
    audio_submission_id: int
    reference: str
    question_id: str
    kind: str
    mode: str
    storage_key: str
    file_size: int
    mime_type: str


def load_private_audio(item: WorkItem) -> bytes:
    """Read an already saved private S3 recording with size/ownership guards."""
    import storage  # Existing Himma S3 client, configured server-side only.

    if (not item.storage_key.startswith(f"audio/{item.student_id}/")
            or item.file_size <= 0 or item.file_size > storage.MAX_AUDIO_BYTES):
        raise ValueError("Audio file failed ownership or size checks")
    storage.verify_audio(item.storage_key, item.file_size, item.mime_type)
    try:
        response = storage.s3_client.get_object(
            Bucket=storage.S3_BUCKET_NAME, Key=item.storage_key)
        body = response["Body"]
        try:
            audio = body.read(item.file_size + 1)
        finally:
            body.close()
    except Exception as exc:
        raise RuntimeError("Private audio storage could not be read") from exc
    if len(audio) != item.file_size:
        raise ValueError("Stored audio length does not match recording metadata")
    return audio


async def run_one(
    session_factory: Callable[[], Session],
    provider: AzureSpeechProvider,
    *,
    worker_id: str,
    audio_loader: Callable[[WorkItem], bytes] = load_private_audio,
    finalize_academic: bool = False,
) -> str:
    """Process at most one job; return a simple operational status.

    The release-runner may enable finalize_academic ONLY after V2 consumers
    have switched to the native journey. In contract tests it remains disabled.
    """
    if finalize_academic:
        # Resume a previously persisted evidence_ready item before consuming
        # another Azure request. The grade and academic progression are atomic.
        with session_factory() as db:
            try:
                from v2_reading_engine.academic_apply import apply_evaluation
                from v2_reading_engine.academic_journey import continue_native_academic_journey
                pending = db.scalar(
                    select(V2ReadingJob.id)
                    .where(V2ReadingJob.is_current.is_(True),
                           V2ReadingJob.status == "evidence_ready")
                    .order_by(V2ReadingJob.created_at, V2ReadingJob.id)
                    .with_for_update(skip_locked=True).limit(1)
                )
                if pending is not None:
                    apply_evaluation(
                        db, job_id=pending,
                        continue_academic_journey=continue_native_academic_journey,
                    )
                    db.commit()
                    return "applied"
            except Exception:
                db.rollback()
                # Do not fake a success or mark a child wrong. Operational
                # recovery retries this durable evidence in the next cycle.
                return "academic_deferred"

    with session_factory() as db:
        job = claim_reading(db, worker_id=worker_id, lease_seconds=300)
        if job is None:
            db.commit()
            return "idle"
        audio = db.get(AudioSubmission, job.audio_submission_id)
        if audio is None:
            db.rollback()
            return "audio_missing"
        work = WorkItem(
            id=job.id, version=job.version,
            student_id=job.student_id, audio_submission_id=job.audio_submission_id,
            reference=job.reference_text, question_id=job.question_id,
            kind=job.reading_kind, mode=job.learning_mode,
            storage_key=audio.storage_key, file_size=audio.file_size,
            mime_type=audio.mime_type,
        )
        db.commit()

    try:
        audio_data = await asyncio.to_thread(audio_loader, work)
    except ValueError:
        return _store_retry_audio(session_factory, work, worker_id)
    except RuntimeError:
        return _store_failure(session_factory, work, worker_id, "audio_store_unavailable")

    mime = work.mime_type.split(";", 1)[0].strip().lower()
    try:
        result: SpeechEvidence = await provider.transcribe(
            audio_data, mime=mime, reference=work.reference,
            letter_mode=work.kind == "letter",
        )
    except Exception:
        return _store_failure(session_factory, work, worker_id, "provider_exception")

    if not result.provider_usable and result.error_code and (
        result.error_code.startswith(("fast_http_", "short_http_"))
        or result.error_code.endswith("_request_failed")
    ):
        return _store_failure(session_factory, work, worker_id, "provider_unavailable")

    decision = evaluate_reading(
        kind=work.kind, mode=work.mode, reference=work.reference,
        transcript=result.transcript, question_id=work.question_id,
        audio_valid=result.error_code not in {"audio_invalid", "wav_format_invalid"},
        provider_usable=result.provider_usable,
    )
    with session_factory() as db:
        try:
            evidence = record_evidence(
                db, job_id=work.id, worker_id=worker_id,
                expected_version=work.version, decision=decision,
                provider_name="azure_speech", provider_request_id=result.request_id,
                transcript=result.transcript,
            )
            # Persist immutable provider evidence BEFORE attempting to advance
            # the learner. An interrupted academic transition must never
            # trigger a second paid transcription for the same recording.
            db.commit()
        except ReadingConflict:
            db.rollback()
            return "superseded"
        except Exception:
            db.rollback()
            return "evidence_deferred"

    if finalize_academic and evidence is not None:
        with session_factory() as db:
            try:
                from v2_reading_engine.academic_apply import apply_evaluation
                from v2_reading_engine.academic_journey import continue_native_academic_journey
                apply_evaluation(
                    db, job_id=work.id,
                    continue_academic_journey=continue_native_academic_journey,
                )
                db.commit()
                return "applied"
            except ReadingConflict:
                db.rollback()
                return "academic_deferred"
            except Exception:
                db.rollback()
                return "academic_deferred"
    return "evidence_ready" if decision.status != "retry_audio" else "retry_audio"


def _store_failure(session_factory, item: WorkItem, worker_id: str,
                   code: str) -> str:
    with session_factory() as db:
        try:
            job = provider_failure(
                db, job_id=item.id, worker_id=worker_id,
                expected_version=item.version, error_code=code)
            state = job.status
            db.commit()
            return state
        except ReadingConflict:
            db.rollback()
            return "superseded"


def _store_retry_audio(session_factory, item: WorkItem,
                       worker_id: str) -> str:
    decision = evaluate_reading(
        kind=item.kind, mode=item.mode, reference=item.reference,
        transcript=None, question_id=item.question_id,
        audio_valid=False, provider_usable=False,
    )
    with session_factory() as db:
        try:
            record_evidence(db, job_id=item.id, worker_id=worker_id,
                            expected_version=item.version, decision=decision,
                            provider_name="audio_validation",
                            provider_request_id=None, transcript=None)
            db.commit()
        except ReadingConflict:
            db.rollback()
            return "superseded"
    return "retry_audio"
