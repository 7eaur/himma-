"""Sanitized operational telemetry for API request correlation and auth abuse signals.

This is deliberately separate from academic/security AuditLog history. It never
logs credentials, access codes, cookies, authorization headers or raw client IPs.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import time
import uuid

from fastapi import Request

logger = logging.getLogger("himma.ops")
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{8,128}$")


def _digest(value: str) -> str:
    secret = os.environ.get("API_SECRET_KEY", "")
    return hmac.new(secret.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def request_id_for(request: Request) -> str:
    existing = getattr(request.state, "request_id", None)
    if existing:
        return str(existing)
    supplied = (request.headers.get("x-request-id") or "").strip()
    request_id = supplied if _REQUEST_ID_RE.fullmatch(supplied) else uuid.uuid4().hex
    request.state.request_id = request_id
    return request_id


def _emit(event: dict) -> None:
    logger.info(json.dumps(event, ensure_ascii=False, separators=(",", ":")))


async def request_correlation_middleware(request: Request, call_next):
    request_id = request_id_for(request)
    started = time.monotonic()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            json.dumps(
                {
                    "event": "http_request_error",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
        raise

    response.headers["x-request-id"] = request_id
    _emit(
        {
            "event": "http_request",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round((time.monotonic() - started) * 1000, 2),
        }
    )
    return response


def log_auth_security_signal(
    request: Request,
    *,
    scope: str,
    outcome: str,
    identifier: str,
) -> None:
    """Emit a privacy-preserving auth signal without raw identifiers or IPs."""
    client_ip = request.client.host if request.client else "unknown"
    normalized = identifier.strip().casefold()
    _emit(
        {
            "event": "auth_security_signal",
            "request_id": request_id_for(request),
            "scope": scope,
            "outcome": outcome,
            "identifier_hash": _digest(f"identifier:{normalized}"),
            "client_hash": _digest(f"client:{client_ip}"),
        }
    )
