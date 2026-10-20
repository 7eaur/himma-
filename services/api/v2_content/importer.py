"""Idempotently register a validated private release without activating it."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from db.models import ContentRelease
from .compiler import compile_release


class ReleaseConflict(RuntimeError):
    pass


def _database_manifest(release: dict[str, Any]) -> dict[str, Any]:
    return {
        "state": release["state"],
        "counts": release["counts"],
        "sources": release["sources"],
        "media": [
            {"id": row["id"], "kind": row.get("kind") or row.get("type"), "status": row["status"]}
            for row in release["media"]
        ],
    }


def register_candidate_release(db: Session, release: dict[str, Any] | None = None) -> ContentRelease:
    release = release or compile_release()
    current = db.query(ContentRelease).filter(ContentRelease.version == release["version"]).one_or_none()
    if current:
        if current.checksum != release["checksum"]:
            raise ReleaseConflict("release version already exists with a different checksum")
        return current

    row = ContentRelease(
        version=release["version"],
        checksum=release["checksum"],
        schema_version=release["schema_version"],
        status="candidate_not_approved",
        manifest_json=_database_manifest(release),
        is_active=False,
        is_immutable=True,
        released_at=None,
    )
    db.add(row)
    db.flush()
    # The legacy column has a Python default because V1 rows were published at
    # creation. A V2 candidate is explicitly not released until approval.
    row.released_at = None
    db.flush()
    return row
