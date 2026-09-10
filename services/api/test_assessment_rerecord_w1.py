"""W1 assessment rerecord regression: deferred, explicit-open and append-only."""

import assessment
import seed_all
from db.database import SessionLocal
from db.models import AssessmentSession, Attempt, AttemptResponse, AudioSubmission, ContentItem, Student


def _student_login(client):
    response = client.post("/auth/student-login", json={"access_code": "STU001"})
    assert response.status_code == 200


def _researcher_login(client):
    response = client.post("/auth/login", json={
        "username": "researcher1",
        "password": "test-only-researcher-password",
    })
    assert response.status_code == 200


def test_assessment_invalid_audio_rerecord_is_explicit_and_append_only(client, monkeypatch):
    seed_all.run_seed_all()
    _student_login(client)
    monkeypatch.setattr(assessment.storage, "verify_audio", lambda *args, **kwargs: None)

    db = SessionLocal()
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    item = (
        db.query(ContentItem)
        .filter(
            ContentItem.kind == "pretest_question",
            ContentItem.interaction_type.in_(["read_aloud", "timed_read_aloud"]),
        )
        .order_by(ContentItem.order_index, ContentItem.id)
        .first()
    )
    assert item is not None
    step = sorted(item.steps, key=lambda value: value.order_index)[0]
    session = AssessmentSession(
        student_id=student.id,
        session_type="pretest",
        status="in_progress",
    )
    db.add(session)
    db.flush()
    attempt = Attempt(session_id=session.id, item_id=item.id, status="completed")
    db.add(attempt)
    db.flush()
    response = AttemptResponse(
        attempt_id=attempt.id,
        step_id=step.id,
        selected_option_id=None,
        is_correct=None,
    )
    db.add(response)
    db.flush()
    first = AudioSubmission(
        response_id=response.id,
        storage_key=f"audio/{student.id}/assessment-first.webm",
        file_size=128,
        mime_type="audio/webm",
        duration_seconds=1.0,
        status="uploaded",
    )
    db.add(first)
    db.commit()
    session_id = session.id
    item_id = item.id
    step_id = step.id
    response_id = response.id
    first_id = first.id
    first_key = first.storage_key
    first_submitted_at = first.submitted_at
    student_id = student.id
    db.close()

    _researcher_login(client)
    rejected = client.post(f"/review/audio/{first_id}/grade", json={"is_valid": False})
    assert rejected.status_code == 200, rejected.text

    _student_login(client)
    next_before_open = client.get(f"/assessment/session/{session_id}/next")
    assert next_before_open.status_code == 409
    assert "إعادة التسجيل" in next_before_open.json()["detail"]

    tasks = client.get(f"/assessment/session/{session_id}/rerecord-tasks")
    assert tasks.status_code == 200, tasks.text
    assert [task["submission_id"] for task in tasks.json()] == [first_id]

    blocked = client.post(
        f"/assessment/session/{session_id}/attempt/{item_id}/submit",
        json={
            "step_id": step_id,
            "audio_storage_key": f"audio/{student_id}/assessment-blocked.webm",
            "audio_file_size": 128,
            "audio_mime_type": "audio/webm",
            "audio_duration_seconds": 1.0,
            "elapsed_seconds": 2,
        },
        headers={"Idempotency-Key": "assessment-rerecord-before-open"},
    )
    assert blocked.status_code == 409
    assert "افتح مهمة إعادة التسجيل" in blocked.json()["detail"]

    opened = client.post(
        f"/assessment/session/{session_id}/attempt/{item_id}/step/{step_id}/rerecord/start"
    )
    assert opened.status_code == 200, opened.text
    assert opened.json()["submission_id"] == first_id

    next_after_open = client.get(f"/assessment/session/{session_id}/next")
    assert next_after_open.status_code == 200, next_after_open.text
    assert next_after_open.json()["id"] == item_id
    assert next_after_open.json()["steps"][0]["id"] == step_id

    second = client.post(
        f"/assessment/session/{session_id}/attempt/{item_id}/submit",
        json={
            "step_id": step_id,
            "audio_storage_key": f"audio/{student_id}/assessment-second.webm",
            "audio_file_size": 128,
            "audio_mime_type": "audio/webm",
            "audio_duration_seconds": 1.0,
            "elapsed_seconds": 2,
        },
        headers={"Idempotency-Key": "assessment-rerecord-after-open"},
    )
    assert second.status_code == 200, second.text

    db = SessionLocal()
    submissions = (
        db.query(AudioSubmission)
        .filter(AudioSubmission.response_id == response_id)
        .order_by(AudioSubmission.id)
        .all()
    )
    assert len(submissions) == 2
    assert submissions[0].id == first_id
    assert submissions[0].status == "rerecord_required"
    assert submissions[0].storage_key == first_key
    assert submissions[0].submitted_at == first_submitted_at
    assert submissions[1].status == "uploaded"
    assert submissions[1].storage_key.endswith("assessment-second.webm")
    second_id = submissions[1].id
    response = db.query(AttemptResponse).filter(AttemptResponse.id == response_id).one()
    assert response.is_correct is None
    db.close()

    # Old rejected history never re-enters the active review queue.
    _researcher_login(client)
    queue = client.get("/review/pending-audio")
    assert queue.status_code == 200, queue.text
    queued_ids = [row["id"] for row in queue.json()]
    assert first_id not in queued_ids
    assert second_id in queued_ids
