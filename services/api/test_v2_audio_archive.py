"""Reviewed audio archive: supervisor only; exactly latest graded child voice."""
from datetime import datetime, timezone
from uuid import uuid4

from conftest import TestingSessionLocal
from db.learning_models import LessonQuestionResponse, LessonSession, StudentJourney
from db.models import AudioSubmission, Student
from v2_content.importer import register_candidate_release


def test_reviewed_audio_archive_is_private_and_shows_latest_only(student_client):
    assert student_client.get("/v2/review/reviewed-recordings").status_code == 403
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        student_id = student.id
        release = register_candidate_release(db)
        db.add(StudentJourney(student_id=student.id, content_release_id=release.id,
                              current_level=1, current_lesson_id="L1-05"))
        session = LessonSession(student_id=student.id, content_release_id=release.id, lesson_id="L1-05")
        db.add(session); db.flush()
        for n in (1, 2):
            response = LessonQuestionResponse(
                lesson_session_id=session.id, question_id="L1-05-GP-04", role="guided_practice",
                answer_json={"answer": {"audio_storage_key": f"audio/{student.id}/test-{n}.webm"}},
                submit_key=str(uuid4()), attempt_no=n, status="graded",
                is_correct=n == 2, reviewed_at=datetime.now(timezone.utc),
            )
            db.add(response); db.flush()
            db.add(AudioSubmission(
                lesson_response_id=response.id, storage_key=f"audio/{student.id}/test-{n}.webm",
                file_size=2000, mime_type="audio/webm", status="graded",
            ))
        db.commit()
    assert student_client.post("/auth/login", json={
        "username": "researcher1", "password": "test-only-researcher-password",
    }).status_code == 200
    result = student_client.get("/v2/review/reviewed-recordings")
    assert result.status_code == 200, result.text
    body = result.json()
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["student_id"] == student_id
    assert item["question_id"] == "L1-05-GP-04"
    assert item["evaluation_source"] == "supervisor"
    assert item["reading_rubric"] is None  # Older V2 reviews remain readable
    assert item["audio_url"].startswith("/api/v2/review/lessons/")
    assert "storage_key" not in result.text and "test-2.webm" not in result.text
    assert student_client.get("/v2/review/reviewed-recordings?kind=pretest").json()["items"] == []
    assert student_client.get("/v2/review/reviewed-recordings?limit=101").status_code == 422
