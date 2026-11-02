"""Offline native job processor: S3/Azure are injected, not accessed in CI."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from sqlalchemy.orm import sessionmaker

from db.models import AudioSubmission
from db.v2_reading_models import V2ReadingEvaluation, V2ReadingJob
from test_v2_reading_job_store import db, enqueue_assessment, new_v2_assessment
from v2_reading_engine.azure_provider import SpeechEvidence
from v2_reading_engine.worker import run_one


class Provider:
    def __init__(self, transcript="لا", usable=True, error=None):
        self.transcript, self.usable, self.error = transcript, usable, error
        self.calls = []

    async def transcribe(self, audio: bytes, *, mime: str,
                         reference: str, letter_mode: bool):
        self.calls.append((audio, mime, reference, letter_mode))
        return SpeechEvidence(
            self.transcript, "fast-transcription", "ar-OM",
            self.usable, error_code=self.error, request_id="req-contract",
        )


def run(db, provider, loader=None):
    factory = sessionmaker(bind=db.bind, expire_on_commit=False)
    args = {"worker_id": "reading-worker"}
    if loader is not None:
        args["audio_loader"] = loader
    return asyncio.run(run_one(factory, provider, **args))


def test_worker_processes_approved_alias_without_touching_student_grade(db):
    student, release, response, audio = new_v2_assessment(db)
    audio.mime_type = "audio/webm; codecs=opus"
    job = enqueue_assessment(db, student, release, response, audio)
    db.commit()
    provider = Provider(transcript="la.")
    outcome = run(db, provider, lambda item: b"audio-data" * 600)
    db.expire_all()
    assert outcome == "evidence_ready"
    assert db.get(V2ReadingJob, job.id).status == "evidence_ready"
    assert len(provider.calls) == 1
    _, mime, reference, letter_mode = provider.calls[0]
    assert mime == "audio/webm"
    assert reference == "لَ" and letter_mode
    evaluation = db.query(V2ReadingEvaluation).one()
    assert evaluation.evidence_json["matched_alias"] == "la"
    assert evaluation.evidence_json["transcript"] == "la."
    assert db.get(AudioSubmission, audio.id).storage_key.startswith(f"audio/{student.id}/")
    assert response.status == "pending_review"
    assert response.question_score_fraction is None
    assert run(db, provider, lambda item: b"ignored") == "idle"
    assert len(provider.calls) == 1


def test_worker_unrecognized_speech_requests_retry_without_error_grade(db):
    student, release, response, audio = new_v2_assessment(db)
    job = enqueue_assessment(db, student, release, response, audio)
    db.commit()
    provider = Provider(transcript=None, usable=False, error="fast_no_match")
    outcome = run(db, provider, lambda item: b"audio-data" * 600)
    db.expire_all()
    assert outcome == "retry_audio"
    assert db.get(V2ReadingJob, job.id).status == "retry_audio"
    assert db.query(V2ReadingEvaluation).count() == 0
    assert response.is_correct is None


def test_worker_connection_error_is_retryable_without_student_penalty(db):
    student, release, response, audio = new_v2_assessment(db)
    job = enqueue_assessment(db, student, release, response, audio)
    db.commit()
    provider = Provider(transcript=None, usable=False, error="fast_http_503")
    outcome = run(db, provider, lambda item: b"audio-data" * 600)
    db.expire_all()
    assert outcome == "retry_wait"
    assert db.get(V2ReadingJob, job.id).last_error_code == "provider_unavailable"
    assert db.query(V2ReadingEvaluation).count() == 0
    assert response.question_score_fraction is None


def test_audio_load_validation_error_does_not_contact_provider(db):
    student, release, response, audio = new_v2_assessment(db)
    job = enqueue_assessment(db, student, release, response, audio)
    db.commit()
    provider = Provider()
    def corrupt(item):
        raise ValueError("object length mismatch")
    outcome = run(db, provider, corrupt)
    db.expire_all()
    assert outcome == "retry_audio"
    assert db.get(V2ReadingJob, job.id).status == "retry_audio"
    assert not provider.calls
    assert db.query(V2ReadingEvaluation).count() == 0


def test_unavailable_storage_retry_keeps_academic_grade_unmodified(db):
    student, release, response, audio = new_v2_assessment(db)
    job = enqueue_assessment(db, student, release, response, audio)
    db.commit()
    provider = Provider()
    def missing(item):
        raise RuntimeError("object storage unavailable")
    outcome = run(db, provider, missing)
    db.expire_all()
    assert outcome == "retry_wait"
    assert db.get(V2ReadingJob, job.id).last_error_code == "audio_store_unavailable"
    assert db.query(V2ReadingEvaluation).count() == 0


def test_azure_evidence_survives_academic_failure_without_second_provider_call(db, monkeypatch):
    """The original audio is transcribed ONCE even when lesson/placement fails."""
    from sqlalchemy.orm import sessionmaker
    from v2_reading_engine import academic_journey
    from v2_reading_engine.worker import run_one

    student, release, response, audio = new_v2_assessment(db)
    job = enqueue_assessment(db, student, release, response, audio)
    job_id = job.id
    response_id = response.id
    db.commit()

    provider = Provider(transcript="لا", usable=True)
    factory = sessionmaker(bind=db.bind, expire_on_commit=False)
    attempts = []

    def broken_journey(transaction, answer, session):
        attempts.append("failed")
        raise RuntimeError("simulated failed placement")

    monkeypatch.setattr(
        academic_journey, "continue_native_academic_journey", broken_journey,
    )
    outcome = asyncio.run(run_one(
        factory, provider, worker_id="recovery-worker",
        audio_loader=lambda _: b"recording" * 300, finalize_academic=True,
    ))
    assert outcome == "academic_deferred"
    db.expire_all()
    assert db.get(V2ReadingJob, job_id).status == "evidence_ready"
    assert db.query(V2ReadingEvaluation).filter(
        V2ReadingEvaluation.job_id == job_id).count() == 1
    assert db.get(type(response), response_id).is_correct is None
    assert len(provider.calls) == 1

    monkeypatch.setattr(
        academic_journey, "continue_native_academic_journey",
        lambda transaction, answer, session: attempts.append("recovered"),
    )
    resumed = asyncio.run(run_one(
        factory, provider, worker_id="recovery-worker-2",
        audio_loader=lambda _: (_ for _ in ()).throw(
            AssertionError("Azure audio must not be loaded twice")),
        finalize_academic=True,
    ))
    db.expire_all()
    assert resumed == "applied"
    assert attempts == ["failed", "recovered"]
    assert db.get(V2ReadingJob, job_id).status == "applied"
    assert db.get(type(response), response_id).is_correct is True
    assert db.query(V2ReadingEvaluation).filter(
        V2ReadingEvaluation.job_id == job_id).count() == 1
    assert len(provider.calls) == 1


def test_failed_academic_replay_preserves_current_evidence_for_future_recovery(db, monkeypatch):
    """A failed replay must not write partial grades or duplicate provider usage."""
    from sqlalchemy.orm import sessionmaker
    from v2_reading_engine import academic_journey
    from v2_reading_engine.worker import run_one

    student, release, response, audio = new_v2_assessment(db)
    job = enqueue_assessment(db, student, release, response, audio)
    job_id = job.id
    db.commit()
    provider = Provider(transcript="لا")
    factory = sessionmaker(bind=db.bind, expire_on_commit=False)

    def broken(*_):
        raise RuntimeError("deliberate placement conflict")

    monkeypatch.setattr(
        academic_journey, "continue_native_academic_journey", broken,
    )
    for _ in range(2):
        result = asyncio.run(run_one(
            factory, provider, worker_id="failing-worker",
            audio_loader=lambda _: b"audio" * 800,
            finalize_academic=True,
        ))
        assert result == "academic_deferred"
    db.expire_all()
    assert db.get(V2ReadingJob, job_id).status == "evidence_ready"
    assert db.query(V2ReadingEvaluation).count() == 1
    assert response.question_score_fraction is None
    assert len(provider.calls) == 1

