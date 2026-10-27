"""Operational readiness checks for trial/release environments.

`/health` remains a cheap liveness probe. This module backs `/ready`, which
verifies the external services and the exact approved runtime-content/media
contract the API needs before it should receive traffic. A failed dependency,
stale content projection, digest mismatch, or missing approved media keeps
readiness closed. The public report intentionally exposes only component status,
never secrets or raw dependency exceptions.
"""

from __future__ import annotations

import csv
import os
import re
from collections import Counter
from pathlib import Path

import redis
from sqlalchemy import text

from canonical_content_publisher import DB_RUNTIME_VERSION, PUBLISHER_VERSION
from content_approval_contract_2026_09_08 import (
    LEARNING_VERSION,
    POSTTEST_VERSION,
    PRETEST_VERSION,
    VERSION,
)
from content_projection_digest import projection_sha256
from db.database import SessionLocal, engine
from db.models import ContentItem, ContentRelease
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
_EXPECTED_APPROVED_AUDIO = 54

_REPO_ROOT = Path(__file__).resolve().parents[2]
_AUDIO_ROOT = _REPO_ROOT / "assets" / "audio" / "HIMMA_AUDIO_V1"
_AUDIO_MANIFEST = _AUDIO_ROOT / "manifest.csv"
_REQUIRED_APPROVED_AUDIO = {
    "LET-01": "مَ",
    "SYL-13": "سَا",
    "WRD-29": "موز",
    "INS-01": "قصة ليان في المزرعة",
    "INS-02": "قصة نادر في الشاطئ",
}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _config_ready() -> bool:
    return all(bool(os.getenv(name, "").strip()) for name in _REQUIRED_CONFIG)


def _database_ready() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def _valid_sha256(value: object) -> bool:
    return bool(_SHA256_RE.fullmatch(str(value or "").strip().lower()))


def _content_ready() -> bool:
    """Fail closed unless PostgreSQL is the exact attested canonical projection.

    This probe is DB-only: it does not rebuild content or parse repository source
    files. Publication stores both the canonical source-release SHA and a digest
    of the current DB learner projection on every item. Readiness independently
    recomputes the latter from current items/steps/active options/media and closes
    if any learner-visible semantic state drifted after publication.
    """
    db = SessionLocal()
    try:
        items = db.query(ContentItem).all()
        if len(items) != _EXPECTED_TOTAL_ITEMS:
            return False

        active_releases = (
            db.query(ContentRelease)
            .filter(ContentRelease.is_active.is_(True))
            .all()
        )
        if len(active_releases) != 1 or str(active_releases[0].version) != VERSION:
            return False

        kinds = Counter(str(item.kind) for item in items)
        if kinds != Counter({
            "pretest_question": 30,
            "posttest_question": 30,
            "core_activity": 30,
            "reinforcement_activity": _EXPECTED_REINFORCEMENT_ITEMS,
        }):
            return False

        canonical_ids: set[str] = set()
        release_shas: set[str] = set()
        projection_shas: set[str] = set()
        for item in items:
            template = dict(item.template_data or {})
            canonical = str(template.get("canonical_id") or "").strip()
            if not canonical or canonical in canonical_ids:
                return False
            canonical_ids.add(canonical)
            if str(item.status) != "approved":
                return False
            if template.get("canonical_release_version") != VERSION:
                return False
            if template.get("canonical_publisher_version") != PUBLISHER_VERSION:
                return False

            release_sha = str(template.get("canonical_release_sha256") or "").strip().lower()
            projection_sha = str(template.get("canonical_projection_sha256") or "").strip().lower()
            if not _valid_sha256(release_sha) or not _valid_sha256(projection_sha):
                return False
            release_shas.add(release_sha)
            projection_shas.add(projection_sha)

            runtime = template.get("db_runtime") or {}
            if runtime.get("version") != DB_RUNTIME_VERSION:
                return False
            if runtime.get("canonical_release_version") != VERSION:
                return False
            if str(runtime.get("canonical_release_sha256") or "").strip().lower() != release_sha:
                return False

        if len(release_shas) != 1 or len(projection_shas) != 1:
            return False

        pretest = [item for item in items if item.kind == "pretest_question"]
        learning = [item for item in items if item.kind in {"core_activity", "reinforcement_activity"}]
        posttest = [item for item in items if item.kind == "posttest_question"]

        for item in pretest:
            template = item.template_data or {}
            if template.get("pretest_experience_version") != PRETEST_VERSION:
                return False
            if (template.get("pretest_experience") or {}).get("version") != PRETEST_VERSION:
                return False

        for item in learning:
            template = item.template_data or {}
            if template.get("learning_experience_version") != LEARNING_VERSION:
                return False
            experience = template.get("learning_experience") or {}
            if experience.get("version") != LEARNING_VERSION:
                return False
            if len(experience.get("rounds") or []) != len(item.steps):
                return False

        for item in posttest:
            template = item.template_data or {}
            if template.get("posttest_experience_version") != POSTTEST_VERSION:
                return False
            if (template.get("posttest_experience") or {}).get("version") != POSTTEST_VERSION:
                return False

        expected_projection_sha = next(iter(projection_shas))
        return projection_sha256(db) == expected_projection_sha
    except Exception:
        return False
    finally:
        db.close()


def _approved_audio_ready() -> bool:
    """Verify the complete approved audio package and both binary variants.

    This is an operational readiness check, not a student content loader. The
    student runtime remains DB-driven; this probe proves the complete static audio
    package shipped with the release is physically deployable and that the five
    corrective semantic anchors still have their approved meanings.
    """
    try:
        with _AUDIO_MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
            approved = [
                row
                for row in csv.DictReader(handle)
                if str(row.get("status") or "").strip() == "approved"
            ]
        ids = [str(row.get("id") or "").strip() for row in approved]
        if len(approved) != _EXPECTED_APPROVED_AUDIO or len(ids) != len(set(ids)):
            return False
        rows = {asset_id: row for asset_id, row in zip(ids, approved, strict=True)}

        for asset_id, semantic_text in _REQUIRED_APPROVED_AUDIO.items():
            row = rows.get(asset_id)
            if row is None or str(row.get("text_ar") or "").strip() != semantic_text:
                return False
        if "SYL-15" in rows:
            return False

        for asset_id, row in rows.items():
            wav_name = str(row.get("filename_wav") or "").strip()
            mp3_name = str(row.get("filename_mp3") or "").strip()
            if wav_name != f"{asset_id}.wav" or mp3_name != f"{asset_id}.mp3":
                return False
            wav_path = _AUDIO_ROOT / "wav_master" / wav_name
            mp3_path = _AUDIO_ROOT / "web_mp3" / mp3_name
            if not wav_path.is_file() or not mp3_path.is_file():
                return False
            if wav_path.stat().st_size <= 0 or mp3_path.stat().st_size <= 0:
                return False
        return True
    except Exception:
        return False


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
        "approved_audio": _approved_audio_ready(),
        "storage": _storage_ready(),
        "redis": _redis_ready(),
    }
    ready = all(checks.values())
    return {
        "status": "ready" if ready else "not_ready",
        "service": "himma-api",
        "checks": {name: "ok" if passed else "unavailable" for name, passed in checks.items()},
    }
