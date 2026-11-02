"""Atomic academic cutover boundary tests: never write a grade in isolation."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select

from db.learning_models import LessonQuestionResponse, LessonSession, SkillEvidence
from db.models import AudioSubmission, AuditLog
from db.v2_reading_models import V2ReadingJob
from test_v2_reading_job_store import db, enqueue_assessment, new_v2_assessment
from v2_reading_engine.academic_apply import apply_evaluation
from v2_reading_engine.job_store import (
    ReadingConflict, claim_reading, enqueue_reading, record_evidence,
)
from v2_reading_engine.policy import evaluate_reading


def ready_assessment(db):
    student, release, answer, audio = new_v2_assessment(db)
    job = enqueue_assessment(db, student, release, answer, audio)
    now = datetime.now(timezone.utc)
    claim_reading(db, worker_id="worker", now=now)
    decision = evaluate_reading(
        kind="letter", mode="assessment", question_id=answer.question_id,
        reference="لَ", transcript="لا.", audio_valid=True, provider_usable=True,
    )
    record_evidence(
        db, job_id=job.id, worker_id="worker",
        expected_version=job.version, decision=decision,
        provider_name="azure", provider_request_id="req1",
        transcript="لا.", now=now + timedelta(seconds=1),
    )
    return student, release, answer, audio, job


def test_atomic_assessment_grade_updates_only_with_journey_callback(db):
    student, release, answer, audio, job = ready_assessment(db)
    called = []
    def continue_journey(transaction, response, session):
        assert transaction is db
        assert session.student_id == student.id
        assert response.question_score_fraction == Decimal("1")
        called.append("assessment")
    applied = apply_evaluation(
        db, job_id=job.id, continue_academic_journey=continue_journey)
    assert applied
    assert called == ["assessment"]
    assert job.status == "applied"
    assert answer.status == "graded"
    assert answer.is_correct is True
    assert answer.question_score_fraction == Decimal("1")
    assert audio.status == "graded"
    assert db.scalar(select(AuditLog).where(
        AuditLog.action == "v2_reading_auto_graded")) is not None
    assert apply_evaluation(
        db, job_id=job.id,
        continue_academic_journey=lambda *_: called.append("duplicate"),
    ) is False
    assert called == ["assessment"]


def test_transaction_failure_rolls_back_grade_and_audit(db):
    student, release, answer, audio, job = ready_assessment(db)
    db.commit()
    answer_id, job_id, audio_id = answer.id, job.id, audio.id
    def break_lesson(*_):
        raise RuntimeError("academic continuation failed")
    with pytest.raises(RuntimeError, match="academic continuation failed"):
        apply_evaluation(db, job_id=job_id,
                         continue_academic_journey=break_lesson)
    db.rollback()
    db.expire_all()
    assert db.get(V2ReadingJob, job_id).status == "evidence_ready"
    assert db.get(type(answer), answer_id).status == "pending_review"
    assert db.get(type(answer), answer_id).question_score_fraction is None
    assert db.get(AudioSubmission, audio_id).status == "pending_review"
    assert db.scalar(select(AuditLog).where(
        AuditLog.action == "v2_reading_auto_graded")) is None


def test_unrecognized_or_unfinalized_reading_cannot_get_grade(db):
    student, release, answer, audio = new_v2_assessment(db)
    job = enqueue_assessment(db, student, release, answer, audio)
    with pytest.raises(ReadingConflict, match="Unresolved"):
        apply_evaluation(db, job_id=job.id, continue_academic_journey=lambda *_: None)
    assert answer.is_correct is None and answer.question_score_fraction is None


def test_stale_academic_response_cannot_be_overwritten(db):
    student, release, answer, audio, job = ready_assessment(db)
    answer.status = "graded"
    answer.is_correct = False
    with pytest.raises(ReadingConflict):
        apply_evaluation(db, job_id=job.id, continue_academic_journey=lambda *_: None)
    assert answer.is_correct is False


def test_lesson_proof_grade_is_derived_from_same_reading_evaluation(db):
    student, release, old_answer, old_audio = new_v2_assessment(db)
    lesson = LessonSession(
        student_id=student.id, content_release_id=release.id,
        lesson_id="L1-04", stage="guided_practice",
        status="in_progress", step_index=0,
    )
    db.add(lesson)
    db.flush()
    response = LessonQuestionResponse(
        lesson_session_id=lesson.id, question_id="L1-04-GP-02",
        role="guided_practice", answer_json={"answer":{"audio":"private"}},
        submit_key="lesson-test-1", attempt_no=1, status="pending_review",
        is_correct=None,
    )
    db.add(response)
    db.flush()
    proof = SkillEvidence(
        response_id=response.id, lesson_session_id=lesson.id,
        student_id=student.id, content_release_id=release.id,
        question_id=response.question_id, source_kind="lesson",
        role="guided_practice", skill_group="letters",
        evidence_type="read_aloud", review_status="pending_review",
        is_correct=None, counts_for_mastery=False, policy_version="legacy",
    )
    db.add(proof)
    audio = AudioSubmission(
        lesson_response_id=response.id, storage_key=f"audio/{student.id}/lesson.wav",
        file_size=2800, mime_type="audio/wav", status="pending_review",
    )
    db.add(audio)
    db.flush()
    job = enqueue_reading(
        db, student_id=student.id, audio_submission_id=audio.id,
        content_release_id=release.id, question_id=response.question_id,
        reference_text="رَ", reading_kind="letter", learning_mode="training",
    )
    now = datetime.now(timezone.utc)
    claim_reading(db, worker_id="worker", now=now)
    decision = evaluate_reading(
        kind="letter", mode="training", question_id=response.question_id,
        reference="رَ", transcript="را", audio_valid=True, provider_usable=True,
    )
    assert decision.status == "correct"
    record_evidence(
        db, job_id=job.id, worker_id="worker", expected_version=job.version,
        decision=decision, provider_name="azure",
        provider_request_id="req2", transcript="را",
        now=now + timedelta(seconds=1),
    )
    def transition(transaction, answer, current_session):
        assert current_session.id == lesson.id
        current_session.step_index += 1
    assert apply_evaluation(db, job_id=job.id,
                            continue_academic_journey=transition)
    assert response.status == "graded"
    assert response.question_score_fraction == Decimal("1")
    assert proof.review_status == "graded"
    assert proof.is_correct is True
    assert proof.counts_for_mastery is False
    assert lesson.step_index == 1
