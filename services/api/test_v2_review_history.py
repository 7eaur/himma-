"""Supervisor history must preserve revisions but never expose storage keys."""
from uuid import uuid4

from conftest import TestingSessionLocal
from db.learning_models import LessonQuestionResponse
from test_v2_lesson_review import _writing_response, _login_researcher


def test_p08_human_history_is_private_and_preserves_original_rewrite(student_client):
    sid, question_id = _writing_response(student_client)
    with TestingSessionLocal() as db:
        response_id = db.query(LessonQuestionResponse).filter(
            LessonQuestionResponse.lesson_session_id == sid,
            LessonQuestionResponse.question_id == question_id,
        ).one().id
    endpoint = f"/v2/review-history/admin/lesson/{response_id}"
    assert student_client.get(endpoint).status_code in (401, 403)
    _login_researcher(student_client)
    first = student_client.get(endpoint)
    assert first.status_code == 200, first.text
    assert first.json()["original"]["text_response"] == "القلم"
    assert first.json()["retries"] == []
    asked = student_client.post(f"/v2/retries/admin/lesson/{response_id}/request", json={
        "reason": "النص الأول غير واضح، نحتاج كتابة نسخة جديدة لتصحيح القراءة",
    })
    assert asked.status_code == 200, asked.text
    task_id = asked.json()["task_id"]
    assert student_client.post("/auth/student-login", json={"access_code": "STU001"}).status_code == 200
    assert student_client.get(endpoint).status_code in (401, 403)
    sent = student_client.post(f"/v2/retries/student/tasks/{task_id}/submit", json={
        "submit_key": str(uuid4()), "text_response": "باب",
    })
    assert sent.status_code == 200, sent.text
    _login_researcher(student_client)
    history = student_client.get(endpoint)
    assert history.status_code == 200, history.text
    data = history.json()
    assert data["original"]["text_response"] == "القلم"
    assert data["retries"][0]["text_response"] == "باب"
    assert data["retries"][0]["status"] == "submitted"
    assert data["recordings"] == []
    assert "storage_key" not in history.text
    assert "submit_key" not in history.text
    assert student_client.get(
        f"/v2/review-history/admin/lesson/{response_id}/recordings/123456",
    ).status_code == 404
