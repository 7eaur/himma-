"""A10/W2 regression coverage for runtime, auth and recording security boundaries."""

from types import SimpleNamespace

import pytest
from botocore.exceptions import ClientError
from fastapi import HTTPException
from starlette.requests import Request

import auth
import auth_rate_limit
import main
import recordings
from conftest import TestingSessionLocal
from auth_session_state import current_auth_epoch
from db.models import Student
from runtime_flags import (
    runtime_security_ready,
    secure_session_cookie_required,
    validate_runtime_safety,
)
from storage import MAX_AUDIO_BYTES


def test_trial_and_production_require_secure_session_cookie(monkeypatch):
    monkeypatch.setenv("ENV", "trial")
    assert secure_session_cookie_required() is True
    monkeypatch.setenv("ENV", "production")
    assert secure_session_cookie_required() is True
    monkeypatch.setenv("ENV", "development")
    assert secure_session_cookie_required() is False


def test_runtime_readiness_rejects_missing_or_development_security_mode(monkeypatch):
    monkeypatch.setenv("API_SECRET_KEY", "x" * 40)
    monkeypatch.delenv("ENV", raising=False)
    assert runtime_security_ready() is False
    monkeypatch.setenv("ENV", "development")
    assert runtime_security_ready() is False
    monkeypatch.setenv("ENV", "trial")
    assert runtime_security_ready() is True
    monkeypatch.setenv("ENV", "production")
    assert runtime_security_ready() is True


def test_protected_runtime_counts_secret_strength_in_utf8_bytes(monkeypatch):
    monkeypatch.setenv("ENV", "trial")
    monkeypatch.setenv("API_SECRET_KEY", "قصير")
    with pytest.raises(RuntimeError, match="at least 32"):
        validate_runtime_safety()


def test_ready_endpoint_fails_closed_when_runtime_security_mode_is_not_protected(client, monkeypatch):
    monkeypatch.setattr(
        main,
        "readiness_report",
        lambda: {"status": "ready", "service": "himma-api", "checks": {"config": "ok"}},
    )
    monkeypatch.setattr(main, "runtime_security_ready", lambda: False)

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["checks"]["security_mode"] == "unavailable"


def test_cookie_writer_uses_protected_runtime_security_policy(monkeypatch):
    captured = {}

    class ResponseStub:
        def set_cookie(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setenv("ENV", "trial")
    auth._set_token_cookie(ResponseStub(), "token")
    assert captured["secure"] is True
    assert captured["httponly"] is True


def test_auth_limiter_blocks_burst_recovers_and_never_stores_raw_identifier(monkeypatch):
    counters = {}
    ttls = {}
    observed_keys = []

    class RedisStub:
        def eval(self, script, key_count, key, window):
            observed_keys.append(key)
            counters[key] = counters.get(key, 0) + 1
            ttls[key] = int(window)
            return [counters[key], ttls[key]]

        def delete(self, key):
            counters.pop(key, None)
            ttls.pop(key, None)
            return 1

    monkeypatch.setenv("ENV", "trial")
    monkeypatch.setenv("API_SECRET_KEY", "s" * 40)
    monkeypatch.setattr(auth_rate_limit, "_client", RedisStub())
    monkeypatch.setattr(auth_rate_limit, "IP_LIMIT", 20)
    monkeypatch.setattr(auth_rate_limit, "IDENTIFIER_LIMIT", 2)
    request = Request({"type": "http", "client": ("203.0.113.5", 50000), "headers": []})
    identifier = "123456"

    auth_rate_limit.enforce_auth_rate_limit(request, scope="student-login", identifier=identifier)
    auth_rate_limit.enforce_auth_rate_limit(request, scope="student-login", identifier=identifier)
    with pytest.raises(HTTPException) as exc_info:
        auth_rate_limit.enforce_auth_rate_limit(request, scope="student-login", identifier=identifier)

    assert exc_info.value.status_code == 429
    assert "Retry-After" in exc_info.value.headers
    assert all(identifier not in key for key in observed_keys)

    auth_rate_limit.clear_identifier_rate_limit(scope="student-login", identifier=identifier)
    auth_rate_limit.enforce_auth_rate_limit(request, scope="student-login", identifier=identifier)


def test_student_access_code_rotation_revokes_pre_rotation_jwt(student_client):
    assert student_client.get("/profile").status_code == 200
    db = TestingSessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        assert current_auth_epoch(db, actor_role="student", actor_id=student.id) == 0
        student.access_code = "654321"
        db.commit()
        assert current_auth_epoch(db, actor_role="student", actor_id=student.id) == 1
    finally:
        db.close()

    assert student_client.get("/profile").status_code == 401


def test_supervisor_password_rotation_revokes_pre_rotation_jwt(researcher_client):
    assert researcher_client.get("/researcher/account").status_code == 200
    response = researcher_client.post(
        "/researcher/account/password",
        json={
            "current_password": "test-only-researcher-password",
            "new_password": "new-test-only-researcher-password-2026",
        },
    )
    assert response.status_code == 200
    assert researcher_client.get("/researcher/account").status_code == 401


def test_legacy_recording_init_rejects_oversize_before_storage_call(monkeypatch):
    monkeypatch.setattr(
        recordings,
        "_get_s3",
        lambda: (_ for _ in ()).throw(AssertionError("storage must not be called")),
    )
    student = SimpleNamespace(id=17)

    with pytest.raises(HTTPException) as exc_info:
        recordings.init_recording(
            recordings.InitRequest(file_size=MAX_AUDIO_BYTES + 1, mime_type="audio/webm"),
            student=student,
        )

    assert exc_info.value.status_code == 413


def test_legacy_recording_presign_binds_content_length_and_type(monkeypatch):
    captured = {}

    class S3Stub:
        def generate_presigned_url(self, operation, Params, ExpiresIn):
            captured.update({"operation": operation, "params": Params, "expiry": ExpiresIn})
            return "https://storage.invalid/signed"

    monkeypatch.setattr(recordings, "_get_s3", lambda: S3Stub())
    student = SimpleNamespace(id=18)
    requested_size = 4096

    result = recordings.init_recording(
        recordings.InitRequest(file_size=requested_size, mime_type="audio/webm"),
        student=student,
    )

    assert captured["operation"] == "put_object"
    assert captured["params"]["ContentLength"] == requested_size
    assert captured["params"]["ContentType"] == "audio/webm"
    assert result["required_headers"] == {
        "Content-Type": "audio/webm",
        "Content-Length": str(requested_size),
    }


def test_legacy_recording_completion_rejects_and_removes_oversized_object(monkeypatch):
    deleted = []

    class S3Stub:
        def head_object(self, **kwargs):
            return {"ContentLength": MAX_AUDIO_BYTES + 1, "ContentType": "audio/webm"}

        def delete_object(self, **kwargs):
            deleted.append(kwargs)

    monkeypatch.setattr(recordings, "_get_s3", lambda: S3Stub())
    student = SimpleNamespace(id=17)

    with pytest.raises(HTTPException) as exc_info:
        recordings.complete_recording(
            recordings.CompleteRequest(recording_id="r", storage_key="audio/17/r.webm"),
            student=student,
        )

    assert exc_info.value.status_code == 413
    assert deleted == [{"Bucket": recordings.S3_BUCKET_NAME, "Key": "audio/17/r.webm"}]


def test_storage_exception_is_not_exposed_to_recording_client(monkeypatch):
    class S3Stub:
        def head_object(self, **kwargs):
            raise ClientError(
                {"Error": {"Code": "AccessDenied", "Message": "SECRET-INTERNAL-STORAGE-DIAGNOSTIC"}},
                "HeadObject",
            )

    monkeypatch.setattr(recordings, "_get_s3", lambda: S3Stub())
    student = SimpleNamespace(id=19)

    with pytest.raises(HTTPException) as exc_info:
        recordings.complete_recording(
            recordings.CompleteRequest(recording_id="r", storage_key="audio/19/r.webm"),
            student=student,
        )

    assert exc_info.value.status_code == 503
    assert "SECRET-INTERNAL-STORAGE-DIAGNOSTIC" not in str(exc_info.value.detail)
