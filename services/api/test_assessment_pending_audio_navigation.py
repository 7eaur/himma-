"""Assessment audio review is academically blocking but navigation is not.

A learner who submits a reading must be able to continue through the remaining
assessment items while the supervisor reviews that recording. The unresolved
submission still blocks final scoring/placement, and a rerecord request is
surfaced as a deferred task until the learner explicitly opens it.
"""

import assessment
import seed
from db.database import SessionLocal
from db.models import AssessmentSession, Attempt, ContentItem, Student


def test_uploaded_assessment_audio_allows_next_but_blocks_finish(client, monkeypatch):
    seed.run_seed()
    monkeypatch.setattr(assessment.storage, "verify_audio", lambda *_args: None)

    assert client.post(
        "/auth/student-login", json={"access_code": "STU001"}
    ).status_code == 200
    session_id = client.post(
        "/assessment/start", json={"session_type": "pretest"}
    ).json()["id"]

    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        session = db.query(AssessmentSession).filter(
            AssessmentSession.id == session_id,
            AssessmentSession.student_id == student.id,
        ).one()
        audio_item = db.query(ContentItem).filter(
            ContentItem.kind == "pretest_question",
            ContentItem.interaction_type == "read_aloud",
        ).order_by(ContentItem.order_index).first()
        assert audio_item is not None
        attempt = Attempt(session_id=session.id, item_id=audio_item.id, status="in_progress")
        db.add(attempt)
        db.commit()
        student_id = student.id
        item_id = audio_item.id
        step_id = audio_item.steps[0].id
    finally:
        db.close()

    submitted = client.post(
        f"/assessment/session/{session_id}/attempt/{item_id}/submit",
        headers={"Idempotency-Key": "phase-f-pending-audio-0001"},
        json={
            "step_id": step_id,
            "audio_storage_key": f"audio/{student_id}/phase-f-pending.webm",
            "audio_file_size": 512,
            "audio_mime_type": "audio/webm",
            "audio_duration_seconds": 4,
            "elapsed_seconds": 4,
        },
    )
    assert submitted.status_code == 200
    assert submitted.json()["is_correct"] is None

    progress = client.get(f"/assessment/session/{session_id}/progress")
    assert progress.status_code == 200
    assert progress.json()["completed_items"] == 1
    assert progress.json()["completed_steps"] == 1
    assert progress.json()["has_pending_item"] is True

    raw_next = client.get(f"/assessment/session/{session_id}/next")
    assert raw_next.status_code == 200
    assert raw_next.json() is not None
    assert raw_next.json()["id"] != item_id
    next_item_id = raw_next.json()["id"]

    clean_next = client.get(f"/assessment-view/session/{session_id}/next")
    assert clean_next.status_code == 200
    assert clean_next.json() is not None
    assert clean_next.json()["id"] == next_item_id

    # Academic completion remains fail-closed until the pending recording is
    # reviewed even though learner navigation has continued.
    finish = client.post(f"/assessment/session/{session_id}/finish")
    assert finish.status_code == 409
    assert "انتظار المراجعة" in finish.json()["detail"]


def test_rerecord_request_is_deferred_until_student_opens_task(client, monkeypatch):
    seed.run_seed()
    monkeypatch.setattr(assessment.storage, "verify_audio", lambda *_args: None)

    assert client.post(
        "/auth/student-login", json={"access_code": "STU001"}
    ).status_code == 200
    session_id = client.post(
        "/assessment/start", json={"session_type": "pretest"}
    ).json()["id"]

    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        audio_item = db.query(ContentItem).filter(
            ContentItem.kind == "pretest_question",
            ContentItem.interaction_type == "read_aloud",
        ).order_by(ContentItem.order_index).first()
        assert audio_item is not None
        attempt = Attempt(session_id=session_id, item_id=audio_item.id, status="in_progress")
        db.add(attempt)
        db.commit()
        student_id = student.id
        item_id = audio_item.id
        step_id = audio_item.steps[0].id
    finally:
        db.close()

    submitted = client.post(
        f"/assessment/session/{session_id}/attempt/{item_id}/submit",
        headers={"Idempotency-Key": "phase-f-rerecord-audio-0001"},
        json={
            "step_id": step_id,
            "audio_storage_key": f"audio/{student_id}/phase-f-rerecord.webm",
            "audio_file_size": 512,
            "audio_mime_type": "audio/webm",
            "audio_duration_seconds": 4,
            "elapsed_seconds": 4,
        },
    )
    assert submitted.status_code == 200

    continued = client.get(f"/assessment/session/{session_id}/next")
    assert continued.status_code == 200
    assert continued.json()["id"] != item_id
    continued_item_id = continued.json()["id"]

    assert client.post(
        "/auth/login",
        json={
            "username": "researcher1",
            "password": "test-only-researcher-password",
        },
    ).status_code == 200
    pending = client.get("/review/pending-audio")
    assert pending.status_code == 200
    submission_id = next(
        row["id"] for row in pending.json()
        if row["student_id"] == student_id
    )
    rejected = client.post(
        f"/review/audio/{submission_id}/grade",
        json={
            "is_valid": False,
            "target_units": 1,
            "deletions": 0,
            "substitutions": 0,
            "insertions": 0,
        },
    )
    assert rejected.status_code == 200

    assert client.post(
        "/auth/student-login", json={"access_code": "STU001"}
    ).status_code == 200

    tasks = client.get(f"/assessment/session/{session_id}/rerecord-tasks")
    assert tasks.status_code == 200
    task = next(row for row in tasks.json() if row["submission_id"] == submission_id)
    assert task["item_id"] == item_id

    # The rerecord request does not hijack the active path before the learner
    # chooses to open it.
    still_continues = client.get(f"/assessment/session/{session_id}/next")
    assert still_continues.status_code == 200
    assert still_continues.json()["id"] == continued_item_id

    opened = client.post(
        f"/assessment/session/{session_id}/attempt/{item_id}/step/{step_id}/rerecord/start"
    )
    assert opened.status_code == 200
    assert opened.json()["opened"] is True

    rerecord = client.get(f"/assessment/session/{session_id}/next")
    assert rerecord.status_code == 200
    assert rerecord.json()["id"] == item_id
    assert rerecord.json()["steps"][0]["id"] == step_id
