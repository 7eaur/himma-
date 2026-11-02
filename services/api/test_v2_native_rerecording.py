"""Re-record after unrecognized sound without spending a learning attempt."""
from datetime import datetime, timedelta, timezone

import pytest

from db.models import AudioSubmission
from db.v2_reading_models import V2ReadingEvaluation, V2ReadingJob
from test_v2_reading_job_store import db, enqueue_assessment, new_v2_assessment
from v2_audio_leases import audio_upload_binding, track_new_audio_upload
from v2_reading_engine import pinned_reference as pinned
from v2_reading_engine.job_store import (
    ReadingConflict, claim_reading, record_evidence,
)
from v2_reading_engine.policy import evaluate_reading
from v2_reading_engine.re_recording import attach_retry_take, retry_is_allowed


def original_needs_retry(db):
    student, release, response, audio = new_v2_assessment(db)
    job = enqueue_assessment(db, student, release, response, audio)
    now = datetime.now(timezone.utc)
    claim_reading(db, worker_id="azure", now=now)
    undecidable = evaluate_reading(
        kind="letter", mode="assessment", reference="لَ",
        transcript=None, question_id=response.question_id,
        audio_valid=True, provider_usable=False,
    )
    record_evidence(
        db, job_id=job.id, worker_id="azure", expected_version=job.version,
        decision=undecidable, provider_name="azure",
        provider_request_id=None, transcript=None, now=now + timedelta(seconds=1),
    )
    assert job.status == "retry_audio"
    return student, release, response, audio, job


def stage(db, *, student, job, key):
    binding = audio_upload_binding("retry", job.id, job.question_id)
    track_new_audio_upload(
        db, student_id=student.id, storage_key=key, binding_key=binding,
    )


def approved(monkeypatch, question="V2-PRE-Q06", ref="لَ"):
    monkeypatch.setattr(pinned, "_load_pinned_release", lambda *_: {
        "questions": [{
            "id": question, "interaction": "read_aloud", "role": "pretest",
            "evidence_type": "syllable_reading",
            "reading_reference": ref,
            "private_answer": {"rubric": {"reference_text": ref}},
        }],
    })


def test_replacing_unclear_audio_keeps_same_academic_answer_and_no_zero(db, monkeypatch):
    student, release, response, audio, first = original_needs_retry(db)
    approved(monkeypatch)
    key = f"audio/{student.id}/new.audio"
    stage(db, student=student, job=first, key=key)
    retry = attach_retry_take(
        db, student_id=student.id, job_id=first.id,
        storage_key=key, file_size=3000, mime_type="audio/webm",
        duration_seconds=3.0,
    )
    assert retry.id != first.id
    assert retry.assessment_response_id == first.assessment_response_id == response.id
    assert retry.question_id == first.question_id
    assert retry.reference_sha256 == first.reference_sha256
    assert not first.is_current and first.status == "superseded"
    assert retry.is_current and retry.status == "queued"
    assert db.query(V2ReadingJob).filter(V2ReadingJob.is_current.is_(True)).count() == 1
    assert db.query(V2ReadingEvaluation).count() == 0
    assert response.is_correct is None and response.question_score_fraction is None
    assert db.query(AudioSubmission).filter(
        AudioSubmission.assessment_response_id == response.id,
    ).count() == 2
    with pytest.raises(ReadingConflict):
        retry_is_allowed(db, student_id=student.id, job_id=first.id)
    with pytest.raises(ReadingConflict):
        retry_is_allowed(db, student_id=student.id, job_id=retry.id)


def test_exact_retry_replay_does_not_add_another_take(db, monkeypatch):
    student, release, response, audio, first = original_needs_retry(db)
    approved(monkeypatch)
    key = f"audio/{student.id}/same.audio"
    stage(db, student=student, job=first, key=key)
    args = dict(student_id=student.id, job_id=first.id,
                storage_key=key, file_size=3000, mime_type="audio/webm",
                duration_seconds=4.0)
    created = attach_retry_take(db, **args)
    replay = attach_retry_take(db, **args)
    assert created.id == replay.id
    assert db.query(AudioSubmission).filter(
        AudioSubmission.assessment_response_id == response.id).count() == 2
    with pytest.raises(ReadingConflict):
        attach_retry_take(db, **{**args, "file_size": 2999})


def test_no_new_recording_if_audio_does_not_belong_to_child(db, monkeypatch):
    student, release, response, audio, first = original_needs_retry(db)
    approved(monkeypatch)
    with pytest.raises(ReadingConflict):
        attach_retry_take(
            db, student_id=student.id + 1, job_id=first.id,
            storage_key=f"audio/{student.id}/new.audio",
            file_size=3000, mime_type="audio/webm", duration_seconds=1.0)
    assert first.is_current and first.status == "retry_audio"


def test_missing_staged_lease_cannot_create_new_audio(db, monkeypatch):
    student, release, response, audio, first = original_needs_retry(db)
    approved(monkeypatch)
    with pytest.raises(ValueError):
        attach_retry_take(
            db, student_id=student.id, job_id=first.id,
            storage_key=f"audio/{student.id}/unstaged.audio",
            file_size=3000, mime_type="audio/webm", duration_seconds=1.0)
    assert first.is_current


def test_only_unclear_provider_result_can_request_new_take(db, monkeypatch):
    student, release, response, audio = new_v2_assessment(db)
    first = enqueue_assessment(db, student, release, response, audio)
    approved(monkeypatch)
    with pytest.raises(ReadingConflict):
        retry_is_allowed(db, student_id=student.id, job_id=first.id)
    with pytest.raises(ReadingConflict):
        retry_is_allowed(db, student_id=student.id + 9, job_id=first.id)
    with pytest.raises(ReadingConflict):
        attach_retry_take(
            db, student_id=student.id, job_id=first.id,
            storage_key=f"audio/{student.id}/new.audio",
            file_size=3000, mime_type="audio/webm", duration_seconds=1.0)


def test_retry_does_not_use_changed_private_question_target(db, monkeypatch):
    student, release, response, audio, first = original_needs_retry(db)
    approved(monkeypatch, ref="لِ")
    key = f"audio/{student.id}/wrong-reference.audio"
    stage(db, student=student, job=first, key=key)
    db.commit()
    with pytest.raises(ReadingConflict, match="pinned reading policy"):
        attach_retry_take(
            db, student_id=student.id, job_id=first.id, storage_key=key,
            file_size=3000, mime_type="audio/webm", duration_seconds=2.0)
    db.rollback()  # one transaction guards replacement and its pinned evidence
    assert db.query(V2ReadingJob).count() == 1


@pytest.mark.parametrize("length,mime,seconds", [
    (0,"audio/webm",2), (11 * 1024 * 1024,"audio/webm",2),
    (3000,"text/plain",2), (3000,"audio/webm",0), (3000,"audio/webm",901),
])
def test_unusable_retry_metadata_is_rejected(db, monkeypatch, length, mime, seconds):
    student, release, response, audio, first = original_needs_retry(db)
    approved(monkeypatch)
    with pytest.raises(ReadingConflict, match="metadata"):
        attach_retry_take(
            db, student_id=student.id, job_id=first.id,
            storage_key=f"audio/{student.id}/new.audio",
            file_size=length, mime_type=mime, duration_seconds=seconds)
