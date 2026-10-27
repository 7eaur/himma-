from v2_content.compiler import compile_release
from v2_content.contracts import PRIVATE_KEYS


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


def test_candidate_media_distinguishes_fixture_from_approved_temporary(student_client):
    media = compile_release()["media"]
    missing = next(asset for asset in media if asset["status"] in {"missing", "missing_new"})
    fixture = student_client.get(f'/v2/content/candidate/media/{missing["id"]}')
    assert fixture.status_code == 200
    assert fixture.json()["test_only"] is True
    assert fixture.json()["url"].startswith("/api/v2/lessons/test-fixtures/")

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
