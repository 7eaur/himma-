import json
import shutil

import pytest
from sqlalchemy.exc import IntegrityError

from conftest import TestingSessionLocal
from db.learning_models import LessonQuestionResponse, LessonSession, StudentJourney, PrivateContentBankSnapshot
from db.models import ContentRelease, Student
from v2_content.compiler import BANK_FILES, BANK_ROOT, ContentBankError, compile_release
from v2_content.contracts import PRIVATE_KEYS
from v2_content.importer import ReleaseConflict, register_candidate_release
from v2_content.media import MediaProvider
from v2_content.projection import student_manifest, student_question


def _keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _keys(child)


def test_compiler_is_deterministic_and_matches_reviewed_baseline():
    first = compile_release()
    second = compile_release()
    assert first == second
    assert first["state"] == "candidate_not_approved"
    assert first["counts"]["lessons"] == 19
    assert first["counts"]["supports"] == 12
    assert first["counts"]["questions"] == 300
    assert first["counts"]["media"] == 89
    assert first["counts"]["levels"] == {"L1": 6, "L2": 6, "L3": 7}
    assert first["counts"]["media_kinds"] == {"audio": 47, "image": 23, "video": 19}
    assert first["counts"]["skills"] == 13
    assert sum(first["counts"]["interactions"].values()) == 300
    assert sum(first["counts"]["roles"].values()) == 300


def test_compiler_rejects_unknown_media_reference(tmp_path):
    for name in BANK_FILES:
        shutil.copy2(BANK_ROOT / name, tmp_path / name)
    path = tmp_path / BANK_FILES[0]
    document = json.loads(path.read_text(encoding="utf-8"))
    document["questions"][0]["stimulus"]["media"].append({"media_id": "UNKNOWN", "kind": "audio"})
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ContentBankError, match="unknown media"):
        compile_release(tmp_path)


def test_student_projection_is_recursive_private_key_allowlist():
    release = compile_release()
    for question in release["questions"]:
        projected = student_question(question)
        assert PRIVATE_KEYS.isdisjoint(set(_keys(projected)))
        assert "correct_option_ids" not in set(_keys(projected))
        if projected["role"] != "guided_practice":
            assert projected["hint"] is None
    manifest = student_manifest(release)
    assert [len(manifest["levels"][key]) for key in ("L1", "L2", "L3")] == [6, 6, 7]
    assert len(manifest["assessment"]["pretest"]) == 30
    assert len(manifest["assessment"]["posttest"]) == 30


def test_fixture_media_is_test_only_and_blocked_from_publish():
    asset = {"id": "VID-L1-01", "kind": "video", "status": "missing_new"}
    resolved = MediaProvider(environment="test", fixture_enabled=True).resolve(asset)
    assert resolved.state == "ready"
    assert resolved.test_only is True
    with pytest.raises(RuntimeError, match="TEST_ONLY"):
        MediaProvider(environment="test", fixture_enabled=True).assert_publishable([asset])
    with pytest.raises(RuntimeError, match="never be enabled"):
        MediaProvider(environment="production", fixture_enabled=True)
    production = MediaProvider(environment="production", fixture_enabled=False).resolve(asset)
    assert production.test_only is False
    assert production.url is None


def test_candidate_registration_is_idempotent_and_private():
    release = compile_release()
    with TestingSessionLocal() as db:
        first = register_candidate_release(db, release)
        db.commit()
        second = register_candidate_release(db, release)
        assert first.id == second.id
        assert first.is_active is False
        assert first.is_immutable is True
        assert first.released_at is None
        assert "questions" not in first.manifest_json
        assert "private_answer" not in json.dumps(first.manifest_json)
        snapshot = db.query(PrivateContentBankSnapshot).filter(PrivateContentBankSnapshot.content_release_id == first.id).one()
        assert snapshot.checksum == first.checksum
        assert any("private_answer" in q for q in snapshot.payload_json["questions"])

        changed = dict(release, checksum="0" * 64)
        with pytest.raises(ReleaseConflict):
            register_candidate_release(db, changed)


def test_learning_state_is_release_pinned_and_submit_idempotent():
    release = compile_release()
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        content = register_candidate_release(db, release)
        journey = StudentJourney(student_id=student.id, content_release_id=content.id)
        session = LessonSession(student_id=student.id, content_release_id=content.id, lesson_id="L1-01")
        db.add_all([journey, session])
        db.flush()
        assert journey.content_release_id == session.content_release_id
        db.add(LessonQuestionResponse(lesson_session_id=session.id, question_id="L1-01-QP1", role="guided_practice", answer_json={"option_id": "A"}, submit_key="same-request"))
        db.flush()
        db.add(LessonQuestionResponse(lesson_session_id=session.id, question_id="L1-01-QP2", role="guided_practice", answer_json={"option_id": "B"}, submit_key="same-request"))
        with pytest.raises(IntegrityError):
            db.flush()


def test_p07_missing_approved_binary_cannot_be_published():
    import pytest
    asset = {"id": "BAD-MEDIA", "kind": "video", "status": "approved",
             "source_path": "assets/video/not-a-real-file-p07.mp4"}
    resolved = MediaProvider(environment="production", fixture_enabled=False).resolve(asset)
    assert resolved.url is None and resolved.state == "pending"
    with pytest.raises(RuntimeError, match="TEST_ONLY"):
        MediaProvider(environment="production", fixture_enabled=False).assert_publishable([asset])


def test_p07_approved_media_requires_existing_file_and_safe_type():
    from v2_content.media import approved_asset_path
    valid = {"id": "LET-01", "kind": "audio", "status": "approved",
             "source_path": "assets/audio/HIMMA_AUDIO_V1/web_mp3/LET-01.mp3"}
    assert approved_asset_path(valid) is not None
    assert MediaProvider(environment="production", fixture_enabled=False).resolve(valid).test_only is False
    assert approved_asset_path(dict(valid, source_path="../services/api/main.py")) is None
    assert approved_asset_path(dict(valid, kind="image")) is None
    assert approved_asset_path(dict(valid, status="missing_new")) is None


def test_p07_required_media_gate_ignores_unused_bank_assets_without_approving_them():
    from v2_content.readiness import required_media_assets, media_readiness_contract
    release = compile_release()
    needed = required_media_assets(release)
    assert len(needed) == 73
    assert {a["id"] for a in needed}.issubset({a["id"] for a in release["media"]})
    inventory = media_readiness_contract(release, provider=MediaProvider(environment="test", fixture_enabled=True))
    assert inventory["required_assets"] == 73
    assert inventory["unused_assets"] == 16
    assert inventory["published_assets"] == 73
    assert inventory["publishable"] is True
    assert inventory["counts"]["temporary"] == 19
    unused = next(row for row in inventory["items"] if row["asset_id"] == "AUD-L1-03-MA")
    assert not unused["required_for_runtime"] and not unused["publication_blocker"]


def test_p07_production_resolution_points_to_existing_approved_media_route():
    from v2_content.media import approved_asset_path
    asset = {"id": "LET-01", "kind": "audio", "status": "approved",
             "source_path": "assets/audio/HIMMA_AUDIO_V1/web_mp3/LET-01.mp3"}
    assert approved_asset_path(asset) is not None
    resolved = MediaProvider(environment="production", fixture_enabled=False).resolve(asset)
    assert resolved.state == "ready" and resolved.test_only is False
    assert resolved.url == "/api/v2/content/media/LET-01"


def test_p07_approved_media_endpoint_never_serves_unapproved_or_missing_assets(student_client, monkeypatch):
    from v2_content import media as media_module
    import v2_content_api
    assert student_client.get("/v2/content/media/AUD-L1-03-MA").status_code == 404
    approved = {
        "id": "LET-01", "kind": "audio", "status": "approved",
        "source_path": "assets/audio/HIMMA_AUDIO_V1/web_mp3/LET-01.mp3",
    }
    monkeypatch.setattr(v2_content_api, "get_media", lambda asset_id: approved if asset_id == "LET-01" else None)
    res = student_client.get("/v2/content/media/LET-01")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("audio/")
    assert res.headers.get("x-himma-test-only") is None
    approved["source_path"] = "assets/audio/HIMMA_AUDIO_V1/web_mp3/NOT-FOUND.mp3"
    assert student_client.get("/v2/content/media/LET-01").status_code == 404


def test_owner_approved_temporary_video_is_bounded_to_exact_binary():
    from v2_content.media import approved_asset_path
    asset = next(row for row in compile_release()["media"] if row["id"] == "VID-L1-01")
    assert approved_asset_path(asset) is not None
    resolved = MediaProvider(environment="production", fixture_enabled=False).resolve(asset)
    assert resolved.state == "ready" and resolved.temporary and not resolved.test_only
    assert resolved.as_dict()["temporary"] is True
    assert approved_asset_path(dict(asset, source_sha256="0" * 64)) is None
    assert approved_asset_path(dict(asset, shared_temporary_video=False)) is None
    assert approved_asset_path(dict(asset, kind="audio")) is None
    assert approved_asset_path(dict(asset, source_path="assets/video/other.mp4")) is None
