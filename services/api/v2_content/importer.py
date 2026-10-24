"""Idempotently register a validated private release without activating it."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from db.models import ContentRelease
from db.learning_models import PrivateContentBankSnapshot
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


def _write_private_snapshot(db: Session, row: ContentRelease, release: dict[str, Any]) -> None:
    """Persist private answer keys away from the public release metadata."""
    existing = db.query(PrivateContentBankSnapshot).filter(PrivateContentBankSnapshot.content_release_id == row.id).one_or_none()
    if existing:
        if existing.checksum != release["checksum"]:
            raise ReleaseConflict("private bank snapshot checksum mismatch")
        return
    db.add(PrivateContentBankSnapshot(
        content_release_id=row.id, checksum=release["checksum"],
        payload_json={key: release[key] for key in ("version", "checksum", "lessons", "supports", "questions", "media")},
    ))
    db.flush()


def register_candidate_release(db: Session, release: dict[str, Any] | None = None) -> ContentRelease:
    release = release or compile_release()
    current = db.query(ContentRelease).filter(ContentRelease.version == release["version"]).one_or_none()
    if current:
        if current.checksum != release["checksum"]:
            raise ReleaseConflict("release version already exists with a different checksum")
        if "bank_snapshot" in (current.manifest_json or {}):
            current.manifest_json = _database_manifest(release)
            db.flush()
        _write_private_snapshot(db, current, release)
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
    _write_private_snapshot(db, row, release)
    return row
