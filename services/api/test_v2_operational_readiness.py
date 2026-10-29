"""D28 probe follows the actual runtime without accepting fixture media."""
from copy import deepcopy
from hashlib import sha256

import pytest

import readiness
from db.database import SessionLocal
from db.learning_models import PrivateContentBankSnapshot, StudentJourney
from db.models import ContentRelease, Student
from v2_content import operational_readiness as probe
from v2_content.compiler import _canonical
from v2_content.importer import register_candidate_release
from v2_content.repository import get_release


@pytest.mark.parametrize("environment,flag,v2", [
    ("trial", "true", True), ("trial", "false", False),
    ("production", "true", False), ("development", "true", False),
])
def test_probe_policy_matches_student_runtime(monkeypatch, environment, flag, v2):
    monkeypatch.setenv("ENV", environment)
    monkeypatch.setenv("HIMMA_TRIAL_V2_PREVIEW", flag)
    calls = []
    monkeypatch.setattr(probe, "content_ready", lambda: calls.append("v2") or True)
    monkeypatch.setattr(readiness, "_canonical_content_ready", lambda: calls.append("v1") or True)
    assert readiness._content_ready()
    assert calls == ["v2" if v2 else "v1"]
    calls.clear()
    monkeypatch.setattr(probe, "approved_media_ready", lambda: calls.append("v2") or True)
    monkeypatch.setattr(readiness, "_canonical_approved_audio_ready", lambda: calls.append("v1") or True)
    assert readiness._approved_audio_ready()
    assert calls == ["v2" if v2 else "v1"]


def test_current_bank_ready_without_seeding_v1_or_writing_release():
    assert probe.content_ready()
    with SessionLocal() as db:
        assert db.query(ContentRelease).count() == 0
        assert db.query(PrivateContentBankSnapshot).count() == 0


@pytest.mark.parametrize("drift", ["answer", "checksum", "version", "schema", "manifest"])
def test_registered_bank_rejects_drift(drift):
    with SessionLocal() as db:
        row = register_candidate_release(db)
        db.commit()
        assert probe.content_ready()
        if drift == "answer":
            snapshot = db.query(PrivateContentBankSnapshot).one()
            payload = deepcopy(snapshot.payload_json)
            payload["questions"][0]["private_answer"]["correct_option_ids"] = ["tampered"]
            snapshot.payload_json = payload
        elif drift == "manifest":
            manifest = deepcopy(row.manifest_json)
            manifest["counts"]["questions"] = 299
            row.manifest_json = manifest
        else:
            setattr(row, {"schema": "schema_version"}.get(drift, drift), "invalid")
        db.commit()
    assert not probe.content_ready()


def test_historical_pinned_bank_is_checked_and_never_replaced():
    old = deepcopy(get_release())
    old["questions"][0]["prompt_ar"] = "historical prompt"
    old["checksum"] = sha256(_canonical({k: v for k, v in old.items()
                                        if k not in {"version", "checksum"}})).hexdigest()
    old["version"] = f'himma-v2-authoring-0.3-draft+{old["checksum"][:12]}'
    with SessionLocal() as db:
        row = register_candidate_release(db, old)
        student = db.query(Student).one()
        db.add(StudentJourney(student_id=student.id, content_release_id=row.id))
        db.commit()
        assert probe.content_ready()
        db.delete(db.query(PrivateContentBankSnapshot).one())
        db.commit()
        assert not probe.content_ready()
        assert db.query(PrivateContentBankSnapshot).count() == 0
        assert db.query(StudentJourney).one().content_release_id == row.id


def test_current_bank_without_old_snapshot_requires_exact_match():
    with SessionLocal() as db:
        row = register_candidate_release(db)
        db.delete(db.query(PrivateContentBankSnapshot).one())
        db.commit()
        assert probe.content_ready()
        row.checksum = "0" * 64
        db.commit()
        assert not probe.content_ready()


@pytest.mark.parametrize("failure", ["missing", "empty", "temporary_digest", "unlisted"])
def test_media_failure_does_not_fall_back_to_fixture(tmp_path, monkeypatch, failure):
    from v2_content import media
    bank = deepcopy(get_release())
    required = set(probe.usage_map(bank))
    asset = next(a for a in bank["media"] if a["id"] in required and a["kind"] == "video")
    if failure == "unlisted":
        bank["media"].remove(asset)
    elif failure == "temporary_digest":
        asset["source_sha256"] = "0" * 64
    else:
        monkeypatch.setattr(media, "REPO_ROOT", tmp_path)
        if failure == "empty":
            path = tmp_path / asset["source_path"]
            path.parent.mkdir(parents=True)
            path.write_bytes(b"")
    monkeypatch.setenv("ENV", "trial")
    monkeypatch.setenv("HIMMA_TRIAL_V2_PREVIEW", "true")
    monkeypatch.setenv("V2_FIXTURE_MEDIA_ENABLED", "true")
    monkeypatch.setattr(probe, "get_release", lambda: bank)
    assert not probe.content_ready()


def test_probe_sanitizes_content_errors(monkeypatch):
    monkeypatch.setattr(probe, "get_release", lambda: (_ for _ in ()).throw(RuntimeError("private-key")))
    assert probe.content_ready() is False
