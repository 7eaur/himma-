"""Runtime safety and security-mode helpers for Himma."""

from __future__ import annotations

import os
from urllib.parse import urlparse

_PROTECTED_RUNTIME_ENVS = {"trial", "production"}
_MIN_SECRET_BYTES = 32


def runtime_environment() -> str:
    return os.getenv("ENV", "development").strip().lower() or "development"


def protected_runtime() -> bool:
    """Return whether the process is serving a trial/production environment."""
    return runtime_environment() in _PROTECTED_RUNTIME_ENVS


def trial_v2_preview_allowed() -> bool:
    """Opt-in preview of the unapproved V2 bank in a protected trial runtime.

    This does not enable candidate release in production. Student login and
    the protected Redis-backed rate limiting remain mandatory.
    """
    return (
        runtime_environment() == "trial"
        and os.getenv("HIMMA_TRIAL_V2_PREVIEW", "").strip().lower() == "true"
    )


def secure_session_cookie_required() -> bool:
    """Session cookies are Secure in every real learner/supervisor environment."""
    return protected_runtime()


def runtime_security_ready() -> bool:
    """Fail readiness closed unless the process is in a protected security mode.

    `/ready` is a release/trial traffic gate, not a development liveness probe.
    A process with ENV missing/development must therefore never advertise itself
    as ready for real traffic, even if its external dependencies happen to work.
    """
    if not protected_runtime():
        return False
    secret = os.getenv("API_SECRET_KEY", "")
    return len(secret.encode("utf-8")) >= _MIN_SECRET_BYTES


def validate_runtime_safety() -> None:
    """Fail closed for unsafe settings in a real trial or production runtime.

    Audio recording has no development bypass. Submitted recordings remain
    pending for supervisor review until an approved automatic speech provider is
    explicitly governed and enabled. Dependency availability belongs to `/ready`.
    """
    if not protected_runtime():
        return

    secret = os.getenv("API_SECRET_KEY", "")
    if len(secret.encode("utf-8")) < _MIN_SECRET_BYTES:
        raise RuntimeError(
            "API_SECRET_KEY must contain at least 32 characters/UTF-8 bytes in trial/production"
        )

    origins = [value.strip() for value in os.getenv("CORS_ORIGINS", "").split(",") if value.strip()]
    if not origins:
        raise RuntimeError("CORS_ORIGINS must contain explicit origins in trial/production")
    for origin in origins:
        parsed = urlparse(origin)
        local_trial = runtime_environment() == "trial" and parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}
        if origin == "*" or parsed.path not in {"", "/"} or not parsed.netloc or (parsed.scheme != "https" and not local_trial):
            raise RuntimeError("CORS_ORIGINS must contain explicit HTTPS origins (localhost HTTP is trial-only)")
