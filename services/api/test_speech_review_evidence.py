from decimal import Decimal

import seed
from conftest import TestingSessionLocal
from db.models import (
    AssessmentSession,
    Attempt,
    AttemptResponse,
    AudioReview,
    AudioSubmission,
    ContentItem,
    ContentStep,
    Student,
)
from db.speech_models import SpeechAnalysis, SpeechAnalysisJob


def _create_reviewable_submission_with_analysis() -> tuple[int, int, int]:
    seed.run_seed()
    db = TestingSessionLocal()
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    item = db.query(ContentItem).filter(ContentItem.interaction_type == "read_aloud").first()
    assert item is not None
    step = db.query(ContentStep).filter(
        ContentStep.item_id == item.id,
        ContentStep.expected_reading_text.is_not(None),
    ).first()
    assert step is not None

    session = AssessmentSession(
        student_id=student.id,
        session_type="pretest",
        status="in_progress",
    )
    db.add(session)
    db.flush()
    attempt = Attempt(session_id=session.id, item_id=item.id, status="in_progress")
    db.add(attempt)
    db.flush()
    response = AttemptResponse(
        attempt_id=attempt.id,
        step_id=step.id,
        is_correct=None,
        elapsed_seconds=4,
    )
    db.add(response)
    db.flush()
    submission = AudioSubmission(
        response_id=response.id,
        storage_key="tests/review-evidence.webm",
        file_size=2048,
        mime_type="audio/webm",
        duration_seconds=Decimal("2.50"),
        status="uploaded",
    )
    db.add(submission)
    db.flush()
    job = SpeechAnalysisJob(
        submission_id=submission.id,
        status="review_required",
        attempt_count=1,
    )
    db.add(job)
    db.flush()
    analysis = SpeechAnalysis(
        job_id=job.id,
        submission_id=submission.id,
        provider_name="azure-speech",
        provider_model="fast-transcription",
        reference_text=step.expected_reading_text,
        transcript_text="كتب",
        overall_confidence=Decimal("0.870000"),
        decision="review_required",
        correct_count=1,
        deletion_count=0,
        insertion_count=0,
        substitution_count=0,
        duration_seconds=Decimal("2.500"),
        tokens_json=[
            {
                "kind": "correct",
                "reference": step.expected_reading_text,
                "hypothesis": "كتب",
                "reference_index": 0,
                "hypothesis_index": 0,
                "start_seconds": 0.2,
                "end_seconds": 1.1,
                "confidence": 0.87,
            }
        ],
        calibration_version=None,
    )
    db.add(analysis)
    db.commit()
    ids = (submission.id, response.id, student.id)
    db.close()
    return ids


def test_supervisor_queue_exposes_machine_evidence_without_academic_effect(researcher_client):
    submission_id, response_id, student_id = _create_reviewable_submission_with_analysis()

    before = TestingSessionLocal()
    response_before = before.query(AttemptResponse).filter(AttemptResponse.id == response_id).one()
    student_before = before.query(Student).filter(Student.id == student_id).one()
    before_snapshot = (response_before.is_correct, student_before.current_level)
    before.close()

    result = researcher_client.get("/review/pending-audio")
    assert result.status_code == 200
    row = next(item for item in result.json() if item["id"] == submission_id)
    evidence = row["machine_analysis"]

    assert evidence["available"] is True
    assert evidence["provider_name"] == "azure-speech"
    assert evidence["transcript_text"] == "كتب"
    assert evidence["normalized_transcript"] == "كتب"
    assert evidence["overall_confidence"] == 0.87
    assert evidence["decision"] == "review_required"
    assert evidence["correct_count"] == 1
    assert evidence["deletion_count"] == 0
    assert evidence["insertion_count"] == 0
    assert evidence["substitution_count"] == 0
    assert evidence["calibration_state"] == "not_calibrated"
    assert evidence["academic_effect"] == "none"
    assert evidence["tokens"][0]["kind"] == "correct"

    after = TestingSessionLocal()
    response_after = after.query(AttemptResponse).filter(AttemptResponse.id == response_id).one()
    student_after = after.query(Student).filter(Student.id == student_id).one()
    assert (response_after.is_correct, student_after.current_level) == before_snapshot
    assert after.query(AudioReview).filter(AudioReview.submission_id == submission_id).count() == 0
    after.close()


def test_student_cannot_read_supervisor_machine_evidence(student_client):
    _create_reviewable_submission_with_analysis()
    result = student_client.get("/review/pending-audio")
    assert result.status_code == 403


def test_queue_handles_pending_analysis_without_fabricating_result(researcher_client):
    seed.run_seed()
    db = TestingSessionLocal()
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    item = db.query(ContentItem).filter(ContentItem.interaction_type == "read_aloud").first()
    assert item is not None
    step = db.query(ContentStep).filter(ContentStep.item_id == item.id).first()
    session = AssessmentSession(student_id=student.id, session_type="pretest", status="in_progress")
    db.add(session)
    db.flush()
    attempt = Attempt(session_id=session.id, item_id=item.id, status="in_progress")
    db.add(attempt)
    db.flush()
    response = AttemptResponse(attempt_id=attempt.id, step_id=step.id, is_correct=None)
    db.add(response)
    db.flush()
    submission = AudioSubmission(
        response_id=response.id,
        storage_key="tests/pending-analysis.webm",
        file_size=1024,
        mime_type="audio/webm",
        status="uploaded",
    )
    db.add(submission)
    db.flush()
    db.add(SpeechAnalysisJob(submission_id=submission.id, status="queued"))
    db.commit()
    submission_id = submission.id
    db.close()

    result = researcher_client.get("/review/pending-audio")
    assert result.status_code == 200
    row = next(item for item in result.json() if item["id"] == submission_id)
    assert row["machine_analysis"] == {
        "available": False,
        "job_status": "queued",
        "decision": None,
        "calibration_state": "not_calibrated",
        "calibration_version": None,
        "academic_effect": "none",
    }
