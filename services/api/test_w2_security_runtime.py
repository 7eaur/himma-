"""A10/W2 regression coverage for runtime and recording security boundaries."""

from types import SimpleNamespace

import pytest
from botocore.exceptions import ClientError
from fastapi import HTTPException

import auth
import main
import recordings
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
