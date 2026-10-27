import pytest

from runtime_flags import validate_runtime_safety


def test_api_rejects_cross_site_mutation(client):
    response = client.post(
        "/auth/student-login",
        json={"access_code": "STU001"},
        headers={"origin": "https://attacker.example", "sec-fetch-site": "cross-site"},
    )
    assert response.status_code == 403


def test_api_accepts_configured_origin(client):
    response = client.post(
        "/auth/student-login",
        json={"access_code": "STU001"},
        headers={"origin": "http://localhost:3000", "sec-fetch-site": "same-site"},
    )
    assert response.status_code == 200


def test_production_cors_is_explicit_https(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("API_SECRET_KEY", "x" * 40)
    for unsafe in ("", "*", "http://himma.example", "https://himma.example/path"):
        monkeypatch.setenv("CORS_ORIGINS", unsafe)
        with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
            validate_runtime_safety()
    monkeypatch.setenv("CORS_ORIGINS", "https://himma.example")
    validate_runtime_safety()
