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


def test_candidate_media_is_explicitly_test_only(student_client):
    asset_id = compile_release()["media"][0]["id"]
    response = student_client.get(f"/v2/content/candidate/media/{asset_id}")
    assert response.status_code == 200
    assert response.json()["test_only"] is True


def test_student_candidate_is_blocked_in_protected_runtime(student_client, monkeypatch):
    monkeypatch.setattr("v2_content_api.protected_runtime", lambda: True)
    response = student_client.get("/v2/content/candidate/manifest")
    assert response.status_code == 503


def test_missing_candidate_resources_are_404(student_client):
    assert student_client.get("/v2/content/candidate/questions/nope").status_code == 404
    assert student_client.get("/v2/content/candidate/media/nope").status_code == 404
