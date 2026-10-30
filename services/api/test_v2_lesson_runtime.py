from uuid import uuid4

from conftest import TestingSessionLocal
from db.learning_models import LessonProgressEvent, LessonSession, PlacementDecisionV2, StudentJourney
from db.models import AssessmentSession, Student, User
from v2_content.importer import register_candidate_release


def _place_fixture(level=1, cursor="L1-01"):
    """Set up an official V2 pretest + audited placement for lesson-only tests."""
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        journey = db.query(StudentJourney).filter(StudentJourney.student_id == student.id).one_or_none()
        if not journey:
            db.add(StudentJourney(
                student_id=student.id, content_release_id=release.id, current_level=level,
                current_lesson_id=cursor, placement_state="placed",
            ))
        else:
            journey.current_level = level
            journey.current_lesson_id = cursor
            journey.placement_state = "placed"
        assessment = db.query(AssessmentSession).filter(
            AssessmentSession.student_id == student.id,
            AssessmentSession.session_type == "pretest",
            AssessmentSession.official_for_reporting.is_(True),
        ).first()
        if not assessment:
            assessment = AssessmentSession(
                student_id=student.id, content_release_id=release.id,
                session_type="pretest", status="completed", v2_state="completed",
                v2_question_index=30, official_for_reporting=True, assigned_level=level,
                final_score=80, assessment_attempt_no=1,
            )
            db.add(assessment)
            db.flush()
            researcher = db.query(User).filter(User.username == "researcher1").one()
            db.add(PlacementDecisionV2(
                student_id=student.id, assessment_session_id=assessment.id,
                content_release_id=release.id, assigned_level=level,
                reason="Official placement fixture for lesson authorization regression",
                policy_version="test-official-placement", decided_by=researcher.id,
            ))
        db.commit()


def _start(student_client, lesson_id="L1-01"):
    _place_fixture()
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
    assert not any(row["preview_enabled"] for row in payload["lessons"])
    assert payload["current_action"] == "placement_required"
    _place_fixture()
    placed = student_client.get("/v2/lessons/catalog").json()
    assert {row["lesson_id"] for row in placed["lessons"] if row["preview_enabled"]} == {"L1-01"}
    assert next(row for row in placed["lessons"] if row["lesson_id"] == "L1-02")["state"] == "locked"


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
    _place_fixture()
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
    ended_key = str(uuid4())
    ended = student_client.post(
        f"/v2/lessons/sessions/{session_id}/events",
        json={"event_key": ended_key, "event_type": "video_ended", "position_seconds": 6, "duration_seconds": 6},
    )
    assert ended.status_code == 200
    # A successful commit followed by a lost HTTP response must be safely
    # acknowledged when the browser retries the same idempotency key.
    retry = student_client.post(
        f"/v2/lessons/sessions/{session_id}/events",
        json={"event_key": ended_key, "event_type": "video_ended", "position_seconds": 6, "duration_seconds": 6},
    )
    assert retry.status_code == 200
    assert retry.json()["session"]["stage"] == "guided_practice"
    assert ended.json()["session"]["stage"] == "guided_practice"
    assert ended.json()["session"]["video_seen"] is True
    resumed = student_client.get(f"/v2/lessons/sessions/{session_id}").json()
    assert resumed["session"]["video_position_seconds"] == 6

    # A slow checkpoint response can arrive after the completion event.
    # Accept the obsolete checkpoint without moving the child backwards,
    # rewinding the saved position, or writing another progress event.
    late_checkpoint = _event(student_client, session_id, "video_progress", position_seconds=2.5, duration_seconds=6)
    assert late_checkpoint.status_code == 200
    assert late_checkpoint.json()["session"]["stage"] == "guided_practice"
    assert late_checkpoint.json()["session"]["video_position_seconds"] == 6
    assert _event(student_client, session_id, "video_ended", position_seconds=6, duration_seconds=6).status_code == 409

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
    assert response.json()["counts"] == {"ready": 87, "pending": 0, "missing": 0, "test_only": 0, "temporary": 19}


def test_student_preview_is_blocked_in_protected_runtime(student_client, monkeypatch):
    monkeypatch.setattr("v2_lesson_runtime.protected_runtime", lambda: True)
    assert student_client.get("/v2/lessons/catalog").status_code == 503
    assert student_client.post("/v2/lessons/L1-01/start").status_code == 503


def test_p07_media_contract_keeps_preview_separate_from_approval(researcher_client):
    response = researcher_client.get("/v2/lessons/admin/media-inventory")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 87
    assert data["counts"] == {"ready": 87, "pending": 0, "missing": 0, "test_only": 0, "temporary": 19}
    assert data["publishable"] is True
    assert data["media_requirements"] == {"audio": 45, "image": 23, "video": 19}
    video = next(x for x in data["items"] if x["asset_id"] == "VID-L1-01")
    assert not video["publication_blocker"] and video["preview_kind"] == "shared_approved_temporary_video" and video["temporary"]
    assert any(r["owner_id"] == "L1-01" for r in video["uses"])
    audio = next(x for x in data["items"] if x["asset_id"] == "AUD-L1-L")
    assert not audio["publication_blocker"] and audio["uses"]
    assert "private_answer" not in response.text


def test_p07_preview_binding_swaps_only_requested_asset_without_runtime_change(student_client, monkeypatch, tmp_path):
    import json
    from v2_lesson_runtime import FIXTURE_VIDEO
    manifest = tmp_path / "bindings.json"
    manifest.write_text(json.dumps({
        "schema": "himma-v2-preview-bindings/1",
        "test_only": True,
        "bindings": {
            "VID-L1-01": {
                "kind": "video",
                "path": "services/api/test_fixtures/himma-v2-video-test-only.mp4"
            }
        },
    }), encoding="utf-8")
    monkeypatch.setattr("v2_lesson_runtime.PREVIEW_BINDINGS_FILE", manifest)
    response = student_client.get("/v2/lessons/test-fixtures/video/VID-L1-01")
    assert response.status_code == 200
    assert response.content == FIXTURE_VIDEO.read_bytes()
    assert response.headers["x-himma-test-only"] == "true"
    other = student_client.get("/v2/lessons/test-fixtures/video/VID-L1-02")
    assert other.status_code == 200
    assert other.headers["x-himma-test-only"] == "true"

    # The exact same renderer refuses an invalid replacement instead of
    # substituting another arbitrary educational video or reading voice.
    manifest.write_text(json.dumps({
        "schema": "himma-v2-preview-bindings/1",
        "bindings": {"VID-L1-01": {"kind": "video", "path": "../../etc/passwd"}},
    }), encoding="utf-8")
    refused = student_client.get("/v2/lessons/test-fixtures/video/VID-L1-01")
    assert refused.status_code == 503

    # Returning to the original mapping does not change Player or API code.
    manifest.unlink()
    restored = student_client.get("/v2/lessons/test-fixtures/video/VID-L1-01")
    assert restored.status_code == 200
    assert restored.headers["x-himma-test-only"] == "true"



def test_p07_supervisor_media_inventory_omits_dormant_assets_from_runtime_gate(researcher_client):
    data = researcher_client.get("/v2/lessons/admin/media-inventory").json()
    assert data["required_assets"] == 73
    assert data["unused_assets"] == 14
    assert data["publishable"] is True
    assert all(row["uses"] for row in data["items"] if row["required_for_runtime"])

def test_p07_preview_bindings_require_explicit_test_only_marker(student_client, monkeypatch, tmp_path):
    import json
    manifest = tmp_path / "bindings.json"
    monkeypatch.setattr("v2_lesson_runtime.PREVIEW_BINDINGS_FILE", manifest)
    manifest.write_text(json.dumps({
        "schema": "himma-v2-preview-bindings/1",
        "test_only": False,
        "bindings": {"VID-L1-01": {
            "kind": "video", "path": "services/api/test_fixtures/himma-v2-video-test-only.mp4"
        }},
    }), encoding="utf-8")
    assert student_client.get("/v2/lessons/test-fixtures/video/VID-L1-01").status_code == 503
    manifest.write_text("[]", encoding="utf-8")
    assert student_client.get("/v2/lessons/test-fixtures/video/VID-L1-01").status_code == 503


def test_p07_unapproved_preview_cannot_read_other_repository_files(student_client, monkeypatch, tmp_path):
    from pathlib import Path
    import v2_lesson_runtime
    original = v2_lesson_runtime.get_media
    monkeypatch.setattr(v2_lesson_runtime, "PREVIEW_BINDINGS_FILE", tmp_path / "absent-preview-map.json")
    def unsafe_file(asset_id):
        asset = original(asset_id)
        if asset_id == "LET-01":
            return dict(asset, source_path="services/api/main.py", v1_path=None, path=None)
        if asset_id == "VOC-04":
            return dict(asset, source_path="services/api/main.py", v1_path=None, path=None)
        return asset
    monkeypatch.setattr(v2_lesson_runtime, "get_media", unsafe_file)
    assert student_client.get("/v2/lessons/test-fixtures/audio/LET-01").status_code == 503
    assert student_client.get("/v2/lessons/test-fixtures/image/VOC-04").status_code == 503
    # Even a path under assets is rejected when its extension is wrong.
    def wrong_extension(asset_id):
        asset = original(asset_id)
        return dict(asset, source_path="assets/brand/ASSET_MANIFEST.json", v1_path=None, path=None)
    monkeypatch.setattr(v2_lesson_runtime, "get_media", wrong_extension)
    assert student_client.get("/v2/lessons/test-fixtures/audio/LET-01").status_code == 503


def test_catalog_uses_v2_placement_level_not_stale_legacy_student_level(student_client):
    # The supervisor's pinned V2 placement must govern which lesson is open
    # even while the legacy Student.current_level field is one level behind.
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        assert student.current_level == 1
        assert db.query(StudentJourney).count() == 0
    _place_fixture(level=2, cursor=None)
    result = student_client.get("/v2/lessons/catalog")
    assert result.status_code == 200, result.text
    rows = result.json()["lessons"]
    assert {r["lesson_id"] for r in rows if r["state"] == "current"} == {"L2-01"}
    assert {r["lesson_id"] for r in rows if r["state"] == "skipped"} == {
        r["lesson_id"] for r in rows if r["level"] == "L1"
    }
    assert next(r for r in rows if r["lesson_id"] == "L1-01")["preview_enabled"] is False
    assert next(r for r in rows if r["lesson_id"] == "L2-02")["state"] == "locked"
    with TestingSessionLocal() as db:
        assert db.query(Student).filter(Student.access_code == "STU001").one().current_level == 1
        assert db.query(StudentJourney).one().current_lesson_id is None

    # The projected fallback must also be actionable, but only by the
    # approved placed-level entry; persist the missing cursor on POST only.
    blocked = student_client.post("/v2/lessons/L2-02/start")
    assert blocked.status_code == 409, blocked.text
    assert blocked.json()["detail"]["current_lesson_id"] == "L2-01"
    started = student_client.post("/v2/lessons/L2-01/start")
    assert started.status_code == 200, started.text
    with TestingSessionLocal() as db:
        assert db.query(StudentJourney).one().current_lesson_id == "L2-01"
        assert db.query(Student).filter(Student.access_code == "STU001").one().current_level == 1


def test_missing_cursor_does_not_bypass_unfinished_pretest(student_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        db.add(StudentJourney(
            student_id=student.id, content_release_id=release.id,
            current_level=2, current_lesson_id=None, placement_state="in_progress",
        ))
        db.commit()
    response = student_client.post("/v2/lessons/L2-01/start")
    assert response.status_code == 409, response.text
    with TestingSessionLocal() as db:
        assert db.query(StudentJourney).one().current_lesson_id is None
        assert db.query(LessonSession).count() == 0


def test_current_action_resumes_active_lesson_before_suggesting_pretest(student_client):
    # A placed student must resume the existing, authorized V2 lesson.
    started = _start(student_client)
    session_id = started["session"]["session_id"]
    current = student_client.get("/v2/assessments/current-action")
    assert current.status_code == 200, current.text
    assert current.json()["action"] == "lesson"
    assert current.json()["href"] == f"/student/learning-v2/{session_id}"
    assert current.json()["state"] == "intro"
    with TestingSessionLocal() as db:
        journey = db.query(StudentJourney).one()
        assert journey.placement_state == "placed"
        assert db.query(LessonSession).filter(LessonSession.id == session_id).one().status == "in_progress"


def test_current_action_prioritizes_pending_assessment_before_active_lesson(student_client):
    # An already submitted pretest can legitimately be waiting for placement.
    # A saved lesson must not override that decision until a supervisor acts.
    _start(student_client)
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        journey = db.query(StudentJourney).filter(StudentJourney.student_id == student.id).one()
        prior = db.query(AssessmentSession).filter(
            AssessmentSession.student_id == student.id,
            AssessmentSession.session_type == "pretest",
            AssessmentSession.official_for_reporting.is_(True),
        ).one()
        # This scenario is an explicitly modeled second pretest attempt.
        # Never reuse attempt #1: PostgreSQL has a unique attempt constraint.
        row = AssessmentSession(
            student_id=student.id, content_release_id=journey.content_release_id,
            session_type="pretest", status="in_progress", v2_state="placement_pending_review",
            v2_question_index=30, v2_policy_version="test",
            assessment_attempt_no=prior.assessment_attempt_no + 1,
            supersedes_session_id=prior.id,
        )
        db.add(row)
        db.commit()
        assessment_id = row.id
    result = student_client.get("/v2/assessments/current-action")
    assert result.status_code == 200, result.text
    payload = result.json()
    assert payload["action"] == "assessment"
    assert payload["state"] == "placement_pending_review"
    assert payload["href"] == f"/student/assessment-v2/{assessment_id}"
    with TestingSessionLocal() as db:
        assert db.query(StudentJourney).one().placement_state == "placed"


def test_current_action_keeps_supervisor_waiting_lesson_resumable(student_client):
    session_id = _start(student_client)["session"]["session_id"]
    with TestingSessionLocal() as db:
        session = db.query(LessonSession).filter(LessonSession.id == session_id).one()
        session.status = "waiting_review"
        session.stage = "waiting_review"
        db.commit()
    response = student_client.get("/v2/assessments/current-action")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["action"] == "lesson"
    assert payload["state"] == "waiting_review"
    assert payload["href"] == f"/student/learning-v2/{session_id}"


def test_direct_start_never_creates_journey_without_official_pretest(student_client):
    catalog = student_client.get("/v2/lessons/catalog").json()
    assert not any(item["preview_enabled"] for item in catalog["lessons"])
    response = student_client.post("/v2/lessons/L1-01/start")
    assert response.status_code == 409, response.text
    assert "الاختبار القبلي" in response.json()["detail"]
    with TestingSessionLocal() as db:
        assert db.query(StudentJourney).count() == 0
        assert db.query(LessonSession).count() == 0


def test_fake_placement_without_official_decision_cannot_unlock_lessons(student_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        db.add(StudentJourney(student_id=student.id, content_release_id=release.id,
                              current_level=1, current_lesson_id="L1-01", placement_state="placed"))
        db.commit()
    catalog = student_client.get("/v2/lessons/catalog").json()
    assert not any(item["preview_enabled"] for item in catalog["lessons"])
    assert student_client.post("/v2/lessons/L1-01/start").status_code == 409
    assert student_client.get("/v2/assessments/current-action").json()["action"] == "placement_review"
    with TestingSessionLocal() as db:
        assert db.query(LessonSession).count() == 0


def test_unplaced_preview_session_cannot_write_events_or_answers(student_client):
    # Existing P03 legacy sessions may remain in storage, but cannot
    # accumulate new academic evidence without an official pretest placement.
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        db.add(StudentJourney(
            student_id=student.id, content_release_id=release.id,
            current_level=1, current_lesson_id="L1-01", placement_state="not_started",
        ))
        row = LessonSession(
            student_id=student.id, content_release_id=release.id,
            lesson_id="L1-01", stage="intro", status="in_progress",
        )
        db.add(row)
        db.commit()
        session_id = row.id
    event = student_client.post(
        f"/v2/lessons/sessions/{session_id}/events",
        json={"event_key": str(uuid4()), "event_type": "intro_complete"},
    )
    assert event.status_code == 409, event.text
    answer = student_client.post(
        f"/v2/lessons/sessions/{session_id}/answers",
        json={"submit_key": str(uuid4()), "selected_option_ids": ["a"]},
    )
    assert answer.status_code == 409, answer.text
    with TestingSessionLocal() as db:
        assert db.query(LessonProgressEvent).count() == 0
        assert db.query(LessonSession).one().stage == "intro"


def test_unplaced_session_never_appears_in_student_catalog_or_resumable_action(student_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        db.add(StudentJourney(student_id=student.id, content_release_id=release.id,
                              current_level=1, current_lesson_id="L1-01", placement_state="not_started"))
        db.add(LessonSession(student_id=student.id, content_release_id=release.id,
                             lesson_id="L1-01", stage="intro", status="in_progress"))
        db.commit()
        lesson_id = db.query(LessonSession.id).scalar()
    catalog = student_client.get("/v2/lessons/catalog")
    assert catalog.status_code == 200, catalog.text
    assert not any(row["preview_enabled"] or row["session_id"] for row in catalog.json()["lessons"])
    current = student_client.get("/v2/assessments/current-action")
    assert current.status_code == 200, current.text
    assert current.json()["action"] == "start_pretest"
    assert student_client.get(f"/v2/lessons/sessions/{lesson_id}").status_code == 409
    assert student_client.get(f"/v2/lessons/sessions/{lesson_id}/interaction").status_code == 409
    assert student_client.get(f"/v2/adaptation/sessions/{lesson_id}/status").status_code == 409
    assert student_client.get(f"/v2/lessons/sessions/{lesson_id}/media/VID-L1-01").status_code == 409


def test_pinned_lesson_video_range_and_private_cache_require_student_session(student_client, client):
    from urllib.parse import urlsplit

    started = _start(student_client)
    session_id = started["session"]["session_id"]
    media_url = started["video"]["url"]
    assert media_url is not None and "?v=" in media_url
    # The same demo binary used by 19 lessons must have ONE stable URL.
    assert media_url.startswith("/api/v2/content/media/VID-L1-01?v=")
    route = media_url.removeprefix("/api")
    media_path = urlsplit(route).path

    partial = student_client.get(route, headers={"Range": "bytes=0-31"})
    assert partial.status_code == 206
    assert partial.headers["cache-control"] == "private, max-age=86400, immutable"
    assert partial.headers["accept-ranges"] == "bytes"
    assert partial.headers["content-range"].startswith("bytes 0-31/")
    assert len(partial.content) == 32
    assert "Cookie" in partial.headers["vary"].split(", ")
    assert student_client.get(media_path).headers["cache-control"] == "private, no-store"
    assert student_client.get(media_path + "?v=" + "0" * 64).status_code == 404
    assert student_client.get(f"/v2/lessons/sessions/{session_id}/media/VID-L3-07").status_code == 404
    # Exercise 401 after removing the cookie from the shared TestClient.
    client.cookies.clear()
    assert client.get(route).status_code == 401


def test_missing_preview_sound_or_image_never_falls_back_to_unrelated_legacy_media(student_client, monkeypatch):
    """An absent educational file must fail closed rather than play a different word."""
    import v2_lesson_runtime

    monkeypatch.setattr(v2_lesson_runtime, "PREVIEW_BINDINGS_FILE", __import__("pathlib").Path("/not-a-binding-file.json"))
    from v2_lesson_runtime import get_media as original_get_media

    def absent_binary(asset_id):
        original = original_get_media(asset_id)
        if asset_id == "LET-01":
            return dict(original, source_path="assets/audio/HIMMA_AUDIO_V1/web_mp3/absent.mp3",
                        v1_path=None, path=None)
        if asset_id == "VOC-04":
            return dict(original, source_path="assets/education/absent-image.webp",
                        v1_path=None, path=None)
        return original

    monkeypatch.setattr(v2_lesson_runtime, "get_media", absent_binary)
    audio = student_client.get("/v2/lessons/test-fixtures/audio/LET-01")
    image = student_client.get("/v2/lessons/test-fixtures/image/VOC-04")
    assert audio.status_code == image.status_code == 503
    assert "غير متاح" in audio.json()["detail"]
    assert "غير متاح" in image.json()["detail"]


def test_shared_temporary_lesson_video_reuses_one_url_across_sessions_and_falls_back_for_changed_bank(student_client, monkeypatch):
    from v2_content.repository import get_release
    from v2_lesson_runtime import _session_payload
    import v2_lesson_runtime
    from copy import deepcopy

    started = _start(student_client)
    first_url = started["video"]["url"]
    with TestingSessionLocal() as db:
        original = db.query(LessonSession).filter(
            LessonSession.id == started["session"]["session_id"],
        ).one()
        second = LessonSession(
            student_id=original.student_id,
            content_release_id=original.content_release_id,
            lesson_id="L1-02",
            stage="complete", status="completed",
        )
        db.add(second)
        db.flush()
        second_payload = _session_payload(db, second)
        assert second_payload["video"]["url"] == first_url
        assert second_payload["video"]["asset_id"] != started["video"]["asset_id"]

        # If today's compiled release changes the temporary video source,
        # a student's frozen release must not resolve to the wrong video.
        current = deepcopy(get_release())
        for row in current["media"]:
            if row.get("kind") == "video":
                row["source_sha256"] = "0" * 64
        monkeypatch.setattr(v2_lesson_runtime, "get_release", lambda: current)
        fallback = _session_payload(db, second)
        assert fallback["video"]["url"].startswith(
            f'/api/v2/lessons/sessions/{second.id}/media/VID-L1-02?v='
        )
