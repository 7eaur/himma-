from v2_content.compiler import compile_release
from v2_content.contracts import PRIVATE_KEYS
from v2_content.readiness import media_readiness_contract
from v2_content.media import MediaProvider


def _all_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _all_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _all_keys(child)


def test_candidate_requires_authentication(client):
    assert client.get("/v2/content/candidate/manifest").status_code == 401


def test_versioned_educational_image_reuses_only_the_exact_binary(student_client):
    from urllib.parse import urlsplit
    resolved = student_client.get("/v2/content/candidate/media/VOC-04").json()
    url = resolved["url"].removeprefix("/api")
    assert "?v=" in url
    image = student_client.get(url)
    assert image.status_code == 200
    assert image.headers["cache-control"] == "private, max-age=86400, immutable"
    assert "Cookie" in image.headers["vary"].split(", ")
    assert image.headers["content-type"].startswith("image/")
    assert student_client.get(urlsplit(url).path).headers["cache-control"] == "private, no-store"
    assert student_client.get(urlsplit(url).path + "?v=" + "0" * 64).status_code == 404
    assert student_client.get("/v2/content/media/LET-01?v=" + "0" * 64).status_code == 404


def test_versioned_educational_image_still_requires_authentication(client):
    from v2_content.repository import get_media
    url = MediaProvider().resolve(get_media("VOC-04")).url.removeprefix("/api")
    assert client.get(url).status_code == 401


def test_student_gets_only_safe_candidate_contract(student_client):
    manifest = student_client.get("/v2/content/candidate/manifest")
    assert manifest.status_code == 200
    assert manifest.json()["counts"]["questions"] == 300
    question_id = compile_release()["questions"][0]["id"]
    response = student_client.get(f"/v2/content/candidate/questions/{question_id}")
    assert response.status_code == 200
    keys = set(_all_keys(response.json()))
    assert PRIVATE_KEYS.isdisjoint(keys)
    assert "correct_option_ids" not in keys


def test_researcher_can_inspect_safe_candidate(researcher_client):
    response = researcher_client.get("/v2/content/candidate/manifest")
    assert response.status_code == 200
    assert response.json()["state"] == "candidate_not_approved"


def test_candidate_media_has_no_unreferenced_missing_audio_and_preserves_approved_temporary(student_client):
    media = compile_release()["media"]
    assert len(media) == 87
    assert all(asset["status"] not in {"missing", "missing_new"} for asset in media)
    for retired in ("AUD-L1-03-MA", "AUD-L1-03-SI"):
        assert student_client.get(f"/v2/content/candidate/media/{retired}").status_code == 404

    temporary = next(asset for asset in media if asset["status"] == "approved_temporary")
    candidate = student_client.get(f'/v2/content/candidate/media/{temporary["id"]}')
    assert candidate.status_code == 200
    assert candidate.json()["temporary"] is True
    assert candidate.json()["test_only"] is False
    assert candidate.json()["url"].startswith("/api/v2/content/media/")



def test_student_candidate_is_blocked_in_protected_runtime(student_client, monkeypatch):
    monkeypatch.setattr("v2_content_api.protected_runtime", lambda: True)
    response = student_client.get("/v2/content/candidate/manifest")
    assert response.status_code == 503


def test_missing_candidate_resources_are_404(student_client):
    assert student_client.get("/v2/content/candidate/questions/nope").status_code == 404
    assert student_client.get("/v2/content/candidate/media/nope").status_code == 404


def test_owner_approved_shared_video_counts_for_current_release_but_stays_temporary():
    bank = compile_release()
    report = media_readiness_contract(bank, provider=MediaProvider(environment="test"))
    videos = [item for item in report["items"]
              if item["kind"] == "video" and item["temporary"] and item["required_for_runtime"]]
    assert len(videos) == 19
    assert all(not item["publication_blocker"] and not item["academic_qa_pending"] for item in videos)
    assert report["publishable"]
    assert report["published_assets"] == report["required_assets"] == 73
    assert report["counts"]["temporary"] == 19



def test_fingerprinted_approved_video_supports_authenticated_range_and_private_reuse(student_client, client):
    from urllib.parse import urlsplit

    asset = next(item for item in compile_release()["media"] if item["kind"] == "video" and item["status"] == "approved_temporary")
    resolved = MediaProvider().resolve(asset)
    assert resolved.url is not None and "?v=" in resolved.url
    path = urlsplit(resolved.url).path.removeprefix("/api")

    partial = student_client.get(path + "?" + urlsplit(resolved.url).query, headers={"Range": "bytes=0-31"})
    assert partial.status_code == 206
    assert partial.headers["cache-control"] == "private, max-age=86400, immutable"
    assert partial.headers["accept-ranges"] == "bytes"
    assert partial.headers["content-range"].startswith("bytes 0-31/")
    assert len(partial.content) == 32
    assert "Cookie" in partial.headers["vary"].split(", ")

    assert student_client.get(path).headers["cache-control"] == "private, no-store"
    assert student_client.get(path + "?v=" + "0" * 64).status_code == 404
    # student_client and client share the same authenticated TestClient fixture.
    client.cookies.clear()
    assert client.get(path + "?" + urlsplit(resolved.url).query, headers={"Range": "bytes=0-31"}).status_code == 401
