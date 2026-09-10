"""Runtime safety and security-mode helpers for Himma."""

from __future__ import annotations

import os

_PROTECTED_RUNTIME_ENVS = {"trial", "production"}
_MIN_SECRET_BYTES = 32


def runtime_environment() -> str:
    return os.getenv("ENV", "development").strip().lower() or "development"


def protected_runtime() -> bool:
    """Return whether the process is serving a trial/production environment."""
    return runtime_environment() in _PROTECTED_RUNTIME_ENVS


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
