"""Authenticated, private V2 audio review history across rerecords."""
from uuid import uuid4

from conftest import TestingSessionLocal
from db.learning_models import LessonQuestionResponse
from test_v2_lesson_review import reading, login_staff, login_student, retry_upload


def test_human_review_history_keeps_original_and_private_audio_revisions(student_client, monkeypatch):
    _, response_id, old_key = reading(student_client, monkeypatch)
    endpoint = f"/v2/review-history/admin/lesson/{response_id}"
    assert student_client.get(endpoint).status_code in (401, 403)

    login_staff(student_client)
    first = student_client.get(endpoint)
    assert first.status_code == 200, first.text
    assert first.json()["original"]["submitted_at"]
    assert "text_response" not in first.json()["original"]
    assert first.json()["retries"] == []
    assert len(first.json()["recordings"]) == 1
    assert "storage_key" not in first.text
    assert old_key not in first.text

    asked = student_client.post(f"/v2/retries/admin/lesson/{response_id}/request", json={
        "reason": "التسجيل الأول غير واضح؛ نحتاج إعادة تسجيل القراءة",
    })
    assert asked.status_code == 200, asked.text
    task_id = asked.json()["task_id"]
    login_student(student_client)
    assert student_client.get(endpoint).status_code in (401, 403)
    replacement = retry_upload(student_client, monkeypatch, task_id)
    sent = student_client.post(f"/v2/retries/student/tasks/{task_id}/submit", json={
        "submit_key": str(uuid4()), **replacement,
    })
    assert sent.status_code == 200, sent.text

    login_staff(student_client)
    history = student_client.get(endpoint)
    assert history.status_code == 200, history.text
    data = history.json()
    assert data["interaction"] == "read_aloud"
    assert data["original"]["submitted_at"]
    assert data["retries"][0]["kind"] == "rerecord"
    assert data["retries"][0]["status"] == "submitted"
    assert "text_response" not in data["retries"][0]
    assert len(data["recordings"]) == 2
    assert any(item["url"] for item in data["recordings"])
    assert "storage_key" not in history.text
    assert "submit_key" not in history.text
    assert old_key not in history.text
    assert replacement["audio_storage_key"] not in history.text
    assert student_client.get(
        f"/v2/review-history/admin/lesson/{response_id}/recordings/123456"
    ).status_code == 404
