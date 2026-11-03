"""Database invariants of native speech evidence, independent of live Azure."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session

from db.models import Base, AssessmentSession, AudioSubmission, ContentRelease, Student
from db.learning_models import AssessmentQuestionResponse, LessonQuestionResponse, LessonSession
from db.v2_reading_models import V2ReadingEvaluation, V2ReadingJob
from v2_reading_engine.policy import evaluate_reading
from v2_reading_engine.job_store import (
    ReadingConflict, claim_reading, enqueue_reading,
    provider_failure, record_evidence,
)


@pytest.fixture
def db():
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def foreign_keys(conn, record):
        conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        yield session
        session.rollback()
    engine.dispose()


def new_v2_assessment(db: Session, *, student: int = 1, question="V2-PRE-Q06"):
    learner = Student(access_code=f"V2TEST{student}", name=f"Learner{student}")
    release = ContentRelease(version=f"V2-native-{student}", is_active=False)
    db.add_all([learner, release])
    db.flush()
    session = AssessmentSession(
        student_id=learner.id, content_release_id=release.id,
        session_type="pretest", status="in_progress", v2_state="answering")
    db.add(session)
    db.flush()
    response = AssessmentQuestionResponse(
        assessment_session_id=session.id, question_id=question, role="pretest",
        answer_json={"audio": "private"}, submit_key=f"key-{student}",
        status="pending_review", is_correct=None,
        skill_group="letter", evidence_type="read_aloud",
    )
    db.add(response)
    db.flush()
    audio = AudioSubmission(
        assessment_response_id=response.id, storage_key=f"audio/{learner.id}/test.wav",
        file_size=3000, mime_type="audio/wav", status="pending_review")
    db.add(audio)
    db.flush()
    return learner, release, response, audio


def enqueue_assessment(db, student, release, response, audio):
    return enqueue_reading(
        db, student_id=student.id, audio_submission_id=audio.id,
        content_release_id=release.id, question_id=response.question_id,
        reference_text="لَ", reading_kind="letter", learning_mode="assessment",
    )


def test_enqueue_is_scoped_to_audio_student_question_and_pinned_release(db):
    student, release, response, audio = new_v2_assessment(db)
    job = enqueue_assessment(db, student, release, response, audio)
    assert job.is_current and job.status == "queued"
    assert enqueue_assessment(db, student, release, response, audio).id == job.id
    with pytest.raises(ReadingConflict, match="bound to another"):
        enqueue_reading(
            db, student_id=student.id, audio_submission_id=audio.id,
            content_release_id=release.id, question_id=response.question_id,
            reference_text="لِ", reading_kind="letter", learning_mode="assessment")
    with pytest.raises(ReadingConflict, match="owned"):
        enqueue_reading(
            db, student_id=1234, audio_submission_id=audio.id,
            content_release_id=release.id, question_id=response.question_id,
            reference_text="لَ", reading_kind="letter", learning_mode="assessment")


def test_claim_and_verified_evidence_are_one_time_and_never_change_old_grades(db):
    student, release, response, audio = new_v2_assessment(db)
    job = enqueue_assessment(db, student, release, response, audio)
    now = datetime.now(timezone.utc)
    claimed = claim_reading(db, worker_id="worker-A", now=now)
    assert claimed.id == job.id
    assert claimed.attempt_count == 1
    assert claimed.status == "processing"
    expected = claimed.version
    decision = evaluate_reading(kind="letter", mode="assessment",
                                reference="لَ", transcript="لا.",
                                question_id=response.question_id,
                                audio_valid=True, provider_usable=True)
    with pytest.raises(ReadingConflict):
        record_evidence(db, job_id=job.id, worker_id="worker-B",
                        expected_version=expected, decision=decision,
                        provider_name="azure", provider_request_id="abc",
                        transcript="لا.", now=now + timedelta(seconds=2))
    evaluation = record_evidence(
        db, job_id=job.id, worker_id="worker-A", expected_version=expected,
        decision=decision, provider_name="azure", provider_request_id="abc",
        transcript="لا.", now=now + timedelta(seconds=2),
    )
    assert evaluation is not None
    assert evaluation.score_fraction == Decimal("1")
    assert evaluation.evidence_json["matched_alias"] == "لا"
    assert evaluation.evidence_json["reference_checksum"] == job.reference_sha256
    assert job.status == "evidence_ready"
    assert db.get(AssessmentQuestionResponse, response.id).status == "pending_review"
    assert db.get(AssessmentQuestionResponse, response.id).is_correct is None
    assert db.get(AssessmentQuestionResponse, response.id).question_score_fraction is None
    with pytest.raises(ReadingConflict):
        record_evidence(db, job_id=job.id, worker_id="worker-A",
                        expected_version=expected, decision=decision,
                        provider_name="azure", provider_request_id=None,
                        transcript="لا.", now=now + timedelta(seconds=3))
    db.flush()
    assert db.query(V2ReadingEvaluation).count() == 1


def test_no_provider_recognition_requests_new_recording_without_zero_grade(db):
    student, release, response, audio = new_v2_assessment(db)
    job = enqueue_assessment(db, student, release, response, audio)
    now = datetime.now(timezone.utc)
    claim_reading(db, worker_id="w1", now=now)
    decision = evaluate_reading(
        kind="letter", mode="assessment", reference="لَ",
        transcript=None, question_id=response.question_id,
        audio_valid=True, provider_usable=False)
    evaluation = record_evidence(
        db, job_id=job.id, worker_id="w1", expected_version=job.version,
        decision=decision, provider_name="azure", provider_request_id=None,
        transcript=None, now=now + timedelta(seconds=1))
    assert evaluation is None
    assert job.status == "retry_audio"
    assert db.query(V2ReadingEvaluation).count() == 0
    assert response.is_correct is None
    assert response.question_score_fraction is None


def test_superseded_recording_cannot_later_become_current(db):
    student, release, response, audio = new_v2_assessment(db)
    old_job = enqueue_assessment(db, student, release, response, audio)
    now = datetime.now(timezone.utc)
    claim_reading(db, worker_id="worker1", now=now)
    failed = evaluate_reading(kind="letter", mode="assessment",
        reference="لَ", transcript=None, question_id=response.question_id,
        audio_valid=True, provider_usable=False)
    record_evidence(db, job_id=old_job.id, worker_id="worker1",
        expected_version=old_job.version, decision=failed,
        provider_name="azure", provider_request_id=None, transcript=None,
        now=now + timedelta(seconds=1))
    replacement = AudioSubmission(
        assessment_response_id=response.id, storage_key=f"audio/{student.id}/later.wav",
        file_size=4000, mime_type="audio/wav", status="uploaded")
    db.add(replacement)
    db.flush()
    new_job = enqueue_assessment(db, student, release, response, replacement)
    assert old_job.status == "superseded" and not old_job.is_current
    assert new_job.is_current and new_job.status == "queued"
    assert new_job.audio_submission_id != old_job.audio_submission_id
    assert db.query(V2ReadingJob).filter(V2ReadingJob.is_current.is_(True)).count() == 1
    with pytest.raises(ReadingConflict):
        record_evidence(db, job_id=old_job.id, worker_id="worker1",
            expected_version=old_job.version, decision=failed,
            provider_name="azure", provider_request_id=None, transcript=None,
            now=now + timedelta(seconds=3))


def test_provider_failures_retry_with_backoff_and_without_academic_penalty(db):
    student, release, response, audio = new_v2_assessment(db)
    job = enqueue_assessment(db, student, release, response, audio)
    now = datetime.now(timezone.utc)
    for attempt in range(1, 4):
        current = claim_reading(db, worker_id=f"worker{attempt}", now=now)
        assert current is job
        assert current.attempt_count == attempt
        status = provider_failure(
            db, job_id=job.id, worker_id=f"worker{attempt}",
            expected_version=job.version, error_code="provider_timeout",
            now=now + timedelta(seconds=1))
        assert status.status == ("retry_wait" if attempt < 3 else "service_unavailable")
        if attempt < 3:
            assert claim_reading(db, worker_id="early", now=now + timedelta(seconds=2)) is None
        now += timedelta(seconds=40)
    assert job.is_current
    assert response.is_correct is None
    assert response.question_score_fraction is None
    assert db.query(V2ReadingEvaluation).count() == 0


def test_expired_worker_lease_does_not_authorize_an_old_worker(db):
    student, release, response, audio = new_v2_assessment(db)
    job = enqueue_assessment(db, student, release, response, audio)
    now = datetime.now(timezone.utc)
    claim_reading(db, worker_id="A", now=now, lease_seconds=15)
    old_version = job.version
    claim_reading(db, worker_id="B", now=now + timedelta(seconds=20))
    assert job.lease_owner == "B"
    bad = evaluate_reading(
        kind="letter", mode="assessment", reference="لَ", transcript="لا",
        question_id=response.question_id, audio_valid=True,
        provider_usable=True)
    with pytest.raises(ReadingConflict):
        record_evidence(db, job_id=job.id, worker_id="A",
            expected_version=old_version, decision=bad,
            provider_name="azure", provider_request_id=None, transcript="لا",
            now=now + timedelta(seconds=25))
    assert job.version != old_version


def test_score_validation_prevents_unauthorized_academic_result(db):
    student, release, response, audio = new_v2_assessment(db)
    job = enqueue_assessment(db, student, release, response, audio)
    now = datetime.now(timezone.utc)
    claim_reading(db, worker_id="worker1", now=now)
    bad = evaluate_reading(kind="letter", mode="assessment",
        reference="لَ", transcript="لا", question_id=response.question_id,
        audio_valid=True, provider_usable=True)
    with pytest.raises(ReadingConflict, match="different reference"):
        record_evidence(db, job_id=job.id, worker_id="worker1",
            expected_version=job.version,
            decision=bad.__class__(**{**bad.__dict__, "reference": "لِ"}),
            provider_name="azure", provider_request_id=None,
            transcript="لا", now=now + timedelta(seconds=1))
    assert db.query(V2ReadingEvaluation).count() == 0


def test_old_fraction_nullable_and_unchanged(db):
    student, release, response, audio = new_v2_assessment(db)
    assert response.question_score_fraction is None
    job = enqueue_assessment(db, student, release, response, audio)
    db.flush()
    assert job.id is not None



def test_provider_outage_reuses_saved_audio_after_cooldown_without_new_grade(db):
    from v2_reading_engine.job_store import retry_saved_audio_after_outage
    student, release, response, audio = new_v2_assessment(db)
    job = enqueue_assessment(db, student, release, response, audio)
    now = datetime.now(timezone.utc)
    for _ in range(3):
        work = claim_reading(db, worker_id="outage-worker", now=now)
        provider_failure(
            db, job_id=work.id, worker_id="outage-worker",
            expected_version=work.version, error_code="provider_timeout",
            now=now + timedelta(seconds=1),
        )
        now += timedelta(seconds=40)
    assert job.status == "service_unavailable"
    with pytest.raises(ReadingConflict, match="cooldown"):
        retry_saved_audio_after_outage(
            db, student_id=student.id, job_id=job.id, now=now,
        )
    with pytest.raises(ReadingConflict):
        retry_saved_audio_after_outage(
            db, student_id=student.id + 1, job_id=job.id,
            now=now + timedelta(minutes=2),
        )
    before = (audio.id, audio.storage_key, response.id, response.is_correct,
              response.question_score_fraction)
    resumed = retry_saved_audio_after_outage(
        db, student_id=student.id, job_id=job.id,
        now=now + timedelta(minutes=2),
    )
    assert resumed.id == job.id and resumed.status == "queued"
    assert resumed.attempt_count == 0 and resumed.lease_owner is None
    assert resumed.is_current
    assert (audio.id, audio.storage_key, response.id, response.is_correct,
            response.question_score_fraction) == before
    with pytest.raises(ReadingConflict):
        retry_saved_audio_after_outage(
            db, student_id=student.id, job_id=job.id,
            now=now + timedelta(minutes=3),
        )
    claimed = claim_reading(db, worker_id="recovery-worker",
                            now=now + timedelta(minutes=3))
    assert claimed.id == job.id and claimed.attempt_count == 1
    assert db.query(V2ReadingEvaluation).count() == 0


def test_outage_recheck_never_uses_purged_audio_or_overwrites_finished_grade(db):
    from v2_reading_engine.job_store import retry_saved_audio_after_outage
    student, release, response, audio = new_v2_assessment(db)
    job = enqueue_assessment(db, student, release, response, audio)
    when = datetime.now(timezone.utc)
    job.status = "service_unavailable"
    job.updated_at = when - timedelta(minutes=3)
    audio.status = "purged"
    with pytest.raises(ReadingConflict, match="not available"):
        retry_saved_audio_after_outage(
            db, student_id=student.id, job_id=job.id, now=when,
        )
    audio.status = "pending_review"
    response.status = "graded"
    response.is_correct = False
    with pytest.raises(ReadingConflict, match="no longer awaiting"):
        retry_saved_audio_after_outage(
            db, student_id=student.id, job_id=job.id, now=when,
        )
