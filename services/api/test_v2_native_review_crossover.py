"""Native speech may never be overridden by historical review endpoints."""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from db.learning_models import LessonQuestionResponse, LessonSession
from db.models import AudioSubmission
from test_v2_reading_job_store import db, enqueue_assessment, new_v2_assessment
from v2_reading_engine.job_store import enqueue_reading
from v2_reading_engine.legacy_review_guard import reject_legacy_review_for_native


def test_existing_assessment_native_job_cannot_be_manual_reviewed_or_requested_again(db):
    student, release, response, audio = new_v2_assessment(db)
    reject_legacy_review_for_native(db, kind="assessment", response_id=response.id)
    enqueue_assessment(db, student, release, response, audio)
    for _ in range(2):
        with pytest.raises(HTTPException) as error:
            reject_legacy_review_for_native(db, kind="assessment", response_id=response.id)
        assert error.value.status_code == 409
        assert "تلقائيًا" in error.value.detail
        assert "Azure" not in error.value.detail
    assert response.is_correct is None


def test_native_lesson_job_cannot_be_claimed_by_staff_and_grading_remains_pending(db):
    student, release, _answer, _audio = new_v2_assessment(db)
    lesson = LessonSession(
        student_id=student.id, content_release_id=release.id,
        lesson_id="L1-04", stage="guided_practice",
        status="in_progress", step_index=0,
    )
    db.add(lesson)
    db.flush()
    response = LessonQuestionResponse(
        lesson_session_id=lesson.id, question_id="L1-04-GP-02",
        role="guided_practice", answer_json={"audio": "private"},
        submit_key="native-review-guard", status="pending_review",
    )
    db.add(response)
    db.flush()
    audio = AudioSubmission(
        lesson_response_id=response.id,
        storage_key=f"audio/{student.id}/guard.webm",
        file_size=4096, mime_type="audio/webm", status="pending_review",
    )
    db.add(audio)
    db.flush()
    reject_legacy_review_for_native(db, kind="lesson", response_id=response.id)
    job = enqueue_reading(
        db, student_id=student.id, audio_submission_id=audio.id,
        content_release_id=release.id, question_id=response.question_id,
        reference_text="رَ", reading_kind="letter", learning_mode="training",
    )
    with pytest.raises(HTTPException) as error:
        reject_legacy_review_for_native(db, kind="lesson", response_id=response.id)
    assert error.value.status_code == 409
    assert response.status == "pending_review" and response.is_correct is None
    assert job.status == "queued"



def test_historical_assessment_queue_does_not_list_active_native_reading(db):
    from db.models import User
    from v2_assessment_runtime import review_queue

    student, release, response, audio = new_v2_assessment(db)
    enqueue_assessment(db, student, release, response, audio)
    staff = User(username="read-only-audit", password_hash="test-only", role="researcher")
    db.add(staff)
    db.flush()
    result = review_queue(limit=20, offset=0, user=staff, db=db)
    assert result["items"] == []
    assert result["blocked_items"] == []
    assert result["next_offset"] is None
    assert response.status == "pending_review"


def test_historical_lesson_queue_excludes_native_job_without_losing_it(db):
    from db.models import User
    from v2_lesson_review import lesson_queue

    student, release, _assessment, _audio = new_v2_assessment(db)
    session = LessonSession(student_id=student.id, content_release_id=release.id,
                            lesson_id="L1-04", stage="guided_practice", status="in_progress")
    db.add(session)
    db.flush()
    response = LessonQuestionResponse(
        lesson_session_id=session.id, question_id="L1-04-GP-02",
        role="guided_practice", answer_json={}, submit_key="queue-boundary",
        status="pending_review",
    )
    db.add(response)
    db.flush()
    audio = AudioSubmission(
        lesson_response_id=response.id, storage_key=f"audio/{student.id}/queue.wav",
        file_size=4096, mime_type="audio/wav", status="pending_review",
    )
    db.add(audio)
    db.flush()
    job = enqueue_reading(
        db, student_id=student.id, audio_submission_id=audio.id,
        content_release_id=release.id, question_id=response.question_id,
        reference_text="رَ", reading_kind="letter", learning_mode="training",
    )
    staff = User(username="lesson-native-audit", password_hash="test-only", role="researcher")
    db.add(staff)
    db.flush()
    result = lesson_queue(limit=20, offset=0, user=staff, db=db)
    assert result["items"] == []
    assert result["blocked_items"] == []
    assert job.status == "queued"
    assert response.is_correct is None


def test_disabled_worker_cannot_queue_reanalysis_of_old_audio(student_client, monkeypatch):
    from v2_reading_engine import runtime
    monkeypatch.setattr(runtime, "native_runtime_configuration", lambda: None)
    response = student_client.post("/v2/reading/jobs/9876/retry-analysis")
    assert response.status_code == 503
    assert "محفوظ" in response.json()["detail"]
