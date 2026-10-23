from uuid import uuid4

from conftest import TestingSessionLocal
from db.learning_models import LessonProgressEvent, LessonSession


def _start(student_client, lesson_id="L1-01"):
    response = student_client.post(f"/v2/lessons/{lesson_id}/start")
    assert response.status_code == 200, response.text
    return response.json()


def _event(student_client, session_id, event_type, **extra):
    return student_client.post(
        f"/v2/lessons/sessions/{session_id}/events",
        json={"event_key": str(uuid4()), "event_type": event_type, **extra},
    )


def test_catalog_is_candidate_test_only_and_requires_student(student_client):
    response = student_client.get("/v2/lessons/catalog")
    assert response.status_code == 200
    payload = response.json()
    assert payload["test_only"] is True
    assert len(payload["lessons"]) == 19
    assert {row["lesson_id"] for row in payload["lessons"] if row["preview_enabled"]} == {"L1-01"}
    assert next(row for row in payload["lessons"] if row["lesson_id"] == "L1-02")["state"] == "locked"


def test_catalog_rejects_researcher(researcher_client):
    assert researcher_client.get("/v2/lessons/catalog").status_code == 403


def test_start_is_release_pinned_resumable_and_other_lesson_is_blocked(student_client):
    first = _start(student_client)
    second = _start(student_client)
    assert first["session"]["session_id"] == second["session"]["session_id"]
    assert first["session"]["stage"] == "intro"
    conflict = student_client.post("/v2/lessons/L2-01/start")
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["session_id"] == first["session"]["session_id"]

    with TestingSessionLocal() as db:
        session = db.query(LessonSession).filter(LessonSession.id == first["session"]["session_id"]).one()
        assert session.content_release_id is not None
        assert session.return_to == {"path": "/student/learning-v2"}


def test_direct_url_cannot_bypass_the_current_lesson_lock(student_client):
    response = student_client.post("/v2/lessons/L1-05/start")
    assert response.status_code == 409
    assert response.json()["detail"]["current_lesson_id"] == "L1-01"
    with TestingSessionLocal() as db:
        assert db.query(LessonSession).count() == 0


def test_intro_video_progress_and_ended_are_persistent_and_idempotent(student_client):
    started = _start(student_client)
    session_id = started["session"]["session_id"]
    intro_key = str(uuid4())
    intro = student_client.post(
        f"/v2/lessons/sessions/{session_id}/events",
        json={"event_key": intro_key, "event_type": "intro_complete"},
    )
    assert intro.status_code == 200
    assert intro.json()["session"]["stage"] == "teaching_video"
    duplicate = student_client.post(
        f"/v2/lessons/sessions/{session_id}/events",
        json={"event_key": intro_key, "event_type": "intro_complete"},
    )
    assert duplicate.status_code == 200

    progress = _event(student_client, session_id, "video_progress", position_seconds=2.5, duration_seconds=6)
    assert progress.status_code == 200
    assert progress.json()["session"]["video_position_seconds"] == 2.5
    too_early = _event(student_client, session_id, "video_ended", position_seconds=4, duration_seconds=6)
    assert too_early.status_code == 409
    ended = _event(student_client, session_id, "video_ended", position_seconds=6, duration_seconds=6)
    assert ended.status_code == 200
    assert ended.json()["session"]["stage"] == "guided_practice"
    assert ended.json()["session"]["video_seen"] is True
    resumed = student_client.get(f"/v2/lessons/sessions/{session_id}").json()
    assert resumed["session"]["video_position_seconds"] == 6

    with TestingSessionLocal() as db:
        assert db.query(LessonProgressEvent).filter(LessonProgressEvent.lesson_session_id == session_id).count() == 3


def test_stage_order_and_cross_student_access_are_enforced(student_client, client):
    started = _start(student_client)
    session_id = started["session"]["session_id"]
    early = _event(student_client, session_id, "video_progress", position_seconds=1, duration_seconds=6)
    assert early.status_code == 409
    client.post("/auth/logout")
    assert client.get(f"/v2/lessons/sessions/{session_id}").status_code == 401


def test_fixture_is_real_private_mp4(student_client):
    response = student_client.get("/v2/lessons/test-fixtures/video/VID-L1-01")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("video/mp4")
    assert response.headers["x-himma-test-only"] == "true"
    assert response.content[4:8] == b"ftyp"
    ranged = student_client.get(
        "/v2/lessons/test-fixtures/video/VID-L1-01",
        headers={"Range": "bytes=0-15"},
    )
    assert ranged.status_code == 206
    assert ranged.headers["accept-ranges"] == "bytes"
    assert ranged.headers["content-range"].startswith("bytes 0-15/")

    audio = student_client.get("/v2/lessons/test-fixtures/audio/LET-04")
    assert audio.status_code == 200
    assert audio.headers["content-type"].startswith("audio/")
    assert audio.headers["x-himma-test-only"] == "true"

    image = student_client.get("/v2/lessons/test-fixtures/image/VOC-04")
    assert image.status_code == 200
    assert image.headers["content-type"].startswith("image/")
    assert image.headers["x-himma-test-only"] == "true"


def test_admin_inventory_reports_source_gaps_not_fixture_readiness(researcher_client):
    response = researcher_client.get("/v2/lessons/admin/media-inventory")
    assert response.status_code == 200
    assert response.json()["counts"] == {"ready": 0, "pending": 56, "missing": 33, "test_only": 89}


def test_student_preview_is_blocked_in_protected_runtime(student_client, monkeypatch):
    monkeypatch.setattr("v2_lesson_runtime.protected_runtime", lambda: True)
    assert student_client.get("/v2/lessons/catalog").status_code == 503
    assert student_client.post("/v2/lessons/L1-01/start").status_code == 503
