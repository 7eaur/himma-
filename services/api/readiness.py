"""Operational readiness checks for trial/release environments.

`/health` remains a cheap liveness probe. This module backs `/ready`, which
verifies the external services and the approved runtime-content contract the
API needs before it should receive traffic. The public report intentionally
exposes only component status, never secrets or raw dependency exceptions.
"""

from __future__ import annotations

import os

import redis
from sqlalchemy import text

from db.database import SessionLocal, engine
from db.models import ContentItem
from storage import S3_BUCKET_NAME, s3_client


_REQUIRED_CONFIG = (
    "DATABASE_URL",
    "API_SECRET_KEY",
    "S3_ACCESS_KEY",
    "S3_SECRET_KEY",
    "S3_BUCKET_NAME",
    "REDIS_URL",
)
_EXPECTED_TOTAL_ITEMS = 125
_EXPECTED_REINFORCEMENT_ITEMS = 35
_STUDENT_EXPERIENCE_VERSION = "HIMMA-STUDENT-EXPERIENCE-2.0"
_DB_RUNTIME_VERSION = "HIMMA-DB-RUNTIME-1.0"
_PRETEST_VERSION = "HIMMA-PRETEST-2026-09-01"


def _config_ready() -> bool:
    return all(bool(os.getenv(name, "").strip()) for name in _REQUIRED_CONFIG)


def _database_ready() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def _content_ready() -> bool:
    """Fail closed when a persistent DB still contains an older content projection."""
    db = SessionLocal()
    try:
        items = db.query(ContentItem).all()
        if len(items) != _EXPECTED_TOTAL_ITEMS:
            return False
        if sum(item.kind == "reinforcement_activity" for item in items) != _EXPECTED_REINFORCEMENT_ITEMS:
            return False

        for item in items:
            template = item.template_data or {}
            if template.get("student_experience_version") != _STUDENT_EXPERIENCE_VERSION:
                return False
            if (template.get("db_runtime") or {}).get("version") != _DB_RUNTIME_VERSION:
                return False

        pretest = [item for item in items if item.kind == "pretest_question"]
        if len(pretest) != 30:
            return False
        if any((item.template_data or {}).get("pretest_experience_version") != _PRETEST_VERSION for item in pretest):
            return False

        learning = [item for item in items if item.kind in {"core_activity", "reinforcement_activity"}]
        posttest = [item for item in items if item.kind == "posttest_question"]
        if len(learning) != 65 or len(posttest) != 30:
            return False
        if any(not (item.template_data or {}).get("learning_experience_version") for item in learning):
            return False
        if any(not (item.template_data or {}).get("posttest_experience_version") for item in posttest):
            return False
        return True
    except Exception:
        return False
    finally:
        db.close()


def _storage_ready() -> bool:
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
        return True
    except Exception:
        return False


def _redis_ready() -> bool:
    redis_url = os.getenv("REDIS_URL", "").strip()
    if not redis_url:
        return False
    try:
        client = redis.Redis.from_url(
            redis_url,
            socket_connect_timeout=1,
            socket_timeout=1,
            decode_responses=False,
        )
        return bool(client.ping())
    except Exception:
        return False


def readiness_report() -> dict[str, object]:
    """Return a sanitized readiness report suitable for an unauthenticated probe."""

    checks = {
        "config": _config_ready(),
        "database": _database_ready(),
        "content": _content_ready(),
        "storage": _storage_ready(),
        "redis": _redis_ready(),
    }
    ready = all(checks.values())
    return {
        "status": "ready" if ready else "not_ready",
        "service": "himma-api",
        "checks": {name: "ok" if passed else "unavailable" for name, passed in checks.items()},
    }
