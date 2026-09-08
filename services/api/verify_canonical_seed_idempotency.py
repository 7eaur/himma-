"""Database-level idempotency gate for the canonical Himma content publisher.

Run after ``alembic upgrade head``. The script publishes the full canonical
release twice against the same database and proves that the second publication:
- keeps the same canonical digest;
- creates/reactivates/retires no option rows;
- creates/retires no current media-link rows;
- keeps durable item/step/option/media/skill/release row identities unchanged.

This is intentionally stronger than checking only the item count.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from db.database import SessionLocal
from db.models import (
    ContentAssetLink,
    ContentItem,
    ContentOption,
    ContentRelease,
    ContentStep,
    Skill,
)
from seed_all import run_seed_all


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _snapshot() -> dict[str, Any]:
    db = SessionLocal()
    try:
        items = [
            {
                "id": int(row.id),
                "stable_key": str(row.stable_key),
                "kind": str(row.kind),
                "level_id": int(row.level_id),
                "skill_id": int(row.skill_id),
                "interaction_type": str(row.interaction_type),
                "order_index": int(row.order_index),
                "version": str(row.version),
                "status": str(row.status),
                "checksum": str(row.checksum),
                "template_data": _jsonable(row.template_data or {}),
            }
            for row in db.query(ContentItem).order_by(ContentItem.id).all()
        ]
        steps = [
            {
                "id": int(row.id),
                "item_id": int(row.item_id),
                "order_index": int(row.order_index),
                "prompt_text": str(row.prompt_text),
                "expected_reading_text": row.expected_reading_text,
            }
            for row in db.query(ContentStep).order_by(ContentStep.id).all()
        ]
        options = [
            {
                "id": int(row.id),
                "step_id": int(row.step_id),
                "text": str(row.text),
                "is_correct": bool(row.is_correct),
                "order_index": int(row.order_index),
                "is_active": bool(row.is_active),
            }
            for row in db.query(ContentOption).order_by(ContentOption.id).all()
        ]
        assets = [
            {
                "id": int(row.id),
                "item_id": int(row.item_id) if row.item_id is not None else None,
                "step_id": int(row.step_id) if row.step_id is not None else None,
                "manifest_asset_id": str(row.manifest_asset_id),
                "asset_type": str(row.asset_type),
                "usage_context": row.usage_context,
            }
            for row in db.query(ContentAssetLink).order_by(ContentAssetLink.id).all()
        ]
        skills = [
            {
                "id": int(row.id),
                "skill_key": str(row.skill_key),
                "name": str(row.name),
                "description": row.description,
                "level_id": int(row.level_id),
                "canonical_skill_id": row.canonical_skill_id,
            }
            for row in db.query(Skill).order_by(Skill.id).all()
        ]
        releases = [
            {
                "id": int(row.id),
                "version": str(row.version),
                "is_active": bool(row.is_active),
                "released_at": _jsonable(row.released_at),
            }
            for row in db.query(ContentRelease).order_by(ContentRelease.id).all()
        ]
        return {
            "items": items,
            "steps": steps,
            "options": options,
            "assets": assets,
            "skills": skills,
            "releases": releases,
        }
    finally:
        db.close()


def _digest(snapshot: dict[str, Any]) -> str:
    raw = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _assert_second_publication_is_noop(result: dict[str, Any]) -> None:
    publication = dict(result.get("publication") or {})
    expected_zero = (
        "option_rows_created",
        "option_rows_reactivated",
        "option_rows_retired",
        "asset_rows_created",
        "asset_rows_retired",
    )
    dirty = {name: int(publication.get(name, -1)) for name in expected_zero if int(publication.get(name, -1)) != 0}
    if dirty:
        raise RuntimeError(f"Second canonical publication changed current rows: {dirty}")
    if int(result.get("additions_created") or 0) != 0:
        raise RuntimeError(f"Second canonical publication recreated reinforcement structure: {result}")


def main() -> None:
    first = run_seed_all()
    first_snapshot = _snapshot()
    first_digest = _digest(first_snapshot)

    second = run_seed_all()
    second_snapshot = _snapshot()
    second_digest = _digest(second_snapshot)

    if first.get("canonical_release_sha256") != second.get("canonical_release_sha256"):
        raise RuntimeError(
            "Canonical release digest changed across repeated publication: "
            f"{first.get('canonical_release_sha256')} != {second.get('canonical_release_sha256')}"
        )
    _assert_second_publication_is_noop(second)

    if first_digest != second_digest:
        sections = [name for name in first_snapshot if first_snapshot[name] != second_snapshot[name]]
        raise RuntimeError(
            "Database content identity changed across repeated canonical publication: "
            f"sections={sections}, first={first_digest}, second={second_digest}"
        )

    print(json.dumps({
        "status": "ok",
        "canonical_release_sha256": second.get("canonical_release_sha256"),
        "database_snapshot_sha256": second_digest,
        "items": len(second_snapshot["items"]),
        "steps": len(second_snapshot["steps"]),
        "options": len(second_snapshot["options"]),
        "asset_links": len(second_snapshot["assets"]),
        "skills": len(second_snapshot["skills"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
