"""Media-only cutover: frozen questions/results stay untouched."""

from copy import deepcopy
from hashlib import sha256
import struct

import pytest

from conftest import TestingSessionLocal
from db.learning_models import PrivateContentBankSnapshot
from test_v2_lesson_runtime import _start
from v2_content.compiler import REPO_ROOT, compile_release
from v2_content.lesson_videos import approved_lesson_videos
from v2_content.media import MediaProvider, approved_asset_path


@pytest.mark.parametrize("asset_id", sorted(approved_lesson_videos()))
def test_approved_video_is_exact_distinct_faststart_mp4(asset_id):
    entry = approved_lesson_videos()[asset_id]
    asset = next(row for row in compile_release()["media"] if row["id"] == asset_id)
    path = approved_asset_path(asset)
    assert path == REPO_ROOT / entry["source_path"]
    data = path.read_bytes()
    assert sha256(data).hexdigest() == entry["source_sha256"]
    assert MediaProvider(environment="production", fixture_enabled=False).resolve(asset).temporary is False
    # Browser metadata must precede media data: no full download before playing.
    atoms = []
    offset = 0
    while offset + 8 <= len(data):
        size, kind = struct.unpack(">I4s", data[offset:offset + 8])
        assert size >= 8
        atoms.append(kind)
        offset += size
    assert atoms.index(b"moov") < atoms.index(b"mdat")


def test_missing_or_corrupt_replacement_never_reverts_to_shared_demo(monkeypatch):
    asset = next(row for row in compile_release()["media"] if row["id"] == "VID-L1-01")
    manifest = deepcopy(approved_lesson_videos())
    manifest[asset["id"]]["source_sha256"] = "0" * 64
    monkeypatch.setattr("v2_content.lesson_videos.approved_lesson_videos", lambda: manifest)
    assert approved_asset_path(asset) is None
    resolved = MediaProvider(environment="production", fixture_enabled=False).resolve(asset)
    assert resolved.url is None and resolved.state == "pending"
    manifest[asset["id"]]["source_path"] = "../../etc/passwd"
    with pytest.raises(ValueError, match="binding"):
        approved_asset_path(asset)


def test_existing_pinned_session_gets_new_video_without_bank_mutation(student_client):
    started = _start(student_client)
    session_id = started["session"]["session_id"]
    with TestingSessionLocal() as db:
        snapshot = db.query(PrivateContentBankSnapshot).one()
        before = deepcopy(snapshot.payload_json)
        assert next(row for row in before["media"] if row["id"] == "VID-L1-01")["shared_temporary_video"] is True
    response = student_client.get(f"/v2/lessons/sessions/{session_id}")
    assert response.status_code == 200
    video = response.json()["video"]
    assert video["asset_id"] == "VID-L1-01" and video["temporary"] is False
    route = video["url"].removeprefix("/api")
    partial = student_client.get(route, headers={"Range": "bytes=1024-1055"})
    path = REPO_ROOT / approved_lesson_videos()["VID-L1-01"]["source_path"]
    assert partial.status_code == 206 and partial.content == path.read_bytes()[1024:1056]
    assert partial.headers["cache-control"] == "private, max-age=86400, immutable"
    assert student_client.get(route.replace("VID-L1-01", "VID-L1-02")).status_code == 404
    with TestingSessionLocal() as db:
        assert db.query(PrivateContentBankSnapshot).one().payload_json == before
