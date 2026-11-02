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
