"""Centralized authentication abuse controls.

The limiter is intentionally active only in protected trial/production runtime.
It uses Redis atomic counters keyed by a keyed digest of the route scope,
request IP and login identifier. Raw student access codes/password identifiers
are never written to Redis. Forwarded headers are deliberately ignored unless a
future trusted-proxy boundary is explicitly configured; ``request.client.host``
is the authority today.
"""

from __future__ import annotations

import hashlib
import hmac
import os

import redis
from fastapi import HTTPException, Request, status

from runtime_flags import protected_runtime

WINDOW_SECONDS = int(os.getenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", "300"))
IP_LIMIT = int(os.getenv("AUTH_RATE_LIMIT_IP_ATTEMPTS", "20"))
IDENTIFIER_LIMIT = int(os.getenv("AUTH_RATE_LIMIT_IDENTIFIER_ATTEMPTS", "8"))

_INCREMENT_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('TTL', KEYS[1])
return {current, ttl}
"""

_client = None


def _redis_client():
    global _client
    if _client is None:
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _client = redis.Redis.from_url(
            url,
            socket_connect_timeout=1,
            socket_timeout=1,
            decode_responses=True,
        )
    return _client


def _digest(value: str) -> str:
    secret = os.environ.get("API_SECRET_KEY", "")
    return hmac.new(
        secret.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _key(scope: str, dimension: str, value: str) -> str:
    return f"himma:auth-limit:{scope}:{dimension}:{_digest(value)}"


def _increment(key: str) -> tuple[int, int]:
    try:
        current, ttl = _redis_client().eval(_INCREMENT_SCRIPT, 1, key, WINDOW_SECONDS)
        return int(current), max(int(ttl), 1)
    except redis.RedisError as exc:
        # Authentication is a protected boundary: if abuse control cannot be
        # enforced in trial/production, fail closed rather than silently bypass.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="خدمة تسجيل الدخول غير متاحة مؤقتًا، حاول مرة أخرى لاحقًا",
        ) from exc


def enforce_auth_rate_limit(request: Request, *, scope: str, identifier: str) -> None:
    if not protected_runtime():
        return

    normalized_identifier = identifier.strip().casefold()
    ip_count, ip_ttl = _increment(_key(scope, "ip", _client_ip(request)))
    identifier_count, identifier_ttl = _increment(
        _key(scope, "identifier", normalized_identifier)
    )
    if ip_count > IP_LIMIT or identifier_count > IDENTIFIER_LIMIT:
        retry_after = max(ip_ttl if ip_count > IP_LIMIT else 0,
                          identifier_ttl if identifier_count > IDENTIFIER_LIMIT else 0,
                          1)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="محاولات تسجيل الدخول كثيرة، حاول مرة أخرى لاحقًا",
            headers={"Retry-After": str(retry_after)},
        )


def clear_identifier_rate_limit(*, scope: str, identifier: str) -> None:
    """Clear only the identifier counter after successful authentication.

    The shared IP counter is intentionally retained so rotating identifiers does
    not bypass abuse protection.
    """
    if not protected_runtime():
        return
    try:
        _redis_client().delete(_key(scope, "identifier", identifier.strip().casefold()))
    except redis.RedisError:
        # Authentication already succeeded. A cleanup failure must not turn that
        # success into a new credential oracle; the window expires naturally.
        return
