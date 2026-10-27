"""Database-level idempotency gate for the canonical Himma content publisher.

Run after ``alembic upgrade head``. The script publishes the full canonical
release twice against the same database and proves that the second publication:
- keeps the same canonical source-release digest and DB projection digest;
- creates/reactivates/retires no option rows;
- creates/retires no current media-link rows;
- keeps durable item/step/option/media/skill/release row identities unchanged;
- leaves exactly the 125-item / 44-skill canonical runtime contract active.

This is intentionally stronger than checking only the item count.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any

from content_approval_contract_2026_09_08 import VERSION
from content_projection_digest import projection_sha256
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

EXPECTED_KIND_COUNTS = {
    "pretest_question": 30,
    "posttest_question": 30,
    "core_activity": 30,
    "reinforcement_activity": 35,
}
EXPECTED_ITEM_COUNT = sum(EXPECTED_KIND_COUNTS.values())
EXPECTED_SKILL_COUNT = 44


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


def _current_projection_sha() -> str:
    db = SessionLocal()
    try:
        return projection_sha256(db)
    finally:
        db.close()


def _digest(snapshot: dict[str, Any]) -> str:
    raw = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _assert_structural_contract(snapshot: dict[str, Any], release_sha: str, projection_sha: str) -> None:
    items = list(snapshot["items"])
    if len(items) != EXPECTED_ITEM_COUNT:
        raise RuntimeError(f"Canonical DB item count mismatch: expected={EXPECTED_ITEM_COUNT} actual={len(items)}")

    kind_counts = Counter(str(item["kind"]) for item in items)
    if dict(kind_counts) != EXPECTED_KIND_COUNTS:
        raise RuntimeError(f"Canonical DB kind counts mismatch: expected={EXPECTED_KIND_COUNTS} actual={dict(kind_counts)}")

    skills = list(snapshot["skills"])
    if len(skills) != EXPECTED_SKILL_COUNT:
        raise RuntimeError(f"Canonical skill count mismatch: expected={EXPECTED_SKILL_COUNT} actual={len(skills)}")
    canonical_skill_keys = {
        f"{int(skill['level_id'])}:{str(skill['canonical_skill_id'] or '')}"
        for skill in skills
        if str(skill["canonical_skill_id"] or "")
    }
    if len(canonical_skill_keys) != EXPECTED_SKILL_COUNT:
        raise RuntimeError(
            "Canonical skills are missing or duplicated after publication: "
            f"rows={len(skills)} canonical_keys={len(canonical_skill_keys)}"
        )

    active_releases = [release for release in snapshot["releases"] if release["is_active"]]
    if len(active_releases) != 1 or active_releases[0]["version"] != VERSION:
        raise RuntimeError(f"Expected exactly one active release {VERSION}, got {active_releases}")

    if len(release_sha) != 64 or len(projection_sha) != 64:
        raise RuntimeError(
            f"Invalid canonical attestation lengths: release={release_sha!r} projection={projection_sha!r}"
        )

    bad_items = []
    for item in items:
        data = dict(item["template_data"] or {})
        if (
            item["status"] != "approved"
            or data.get("canonical_release_version") != VERSION
            or data.get("canonical_release_sha256") != release_sha
            or data.get("canonical_projection_sha256") != projection_sha
        ):
            bad_items.append({
                "id": item["id"],
                "stable_key": item["stable_key"],
                "status": item["status"],
                "version": data.get("canonical_release_version"),
                "release_sha256": data.get("canonical_release_sha256"),
                "projection_sha256": data.get("canonical_projection_sha256"),
            })
    if bad_items:
        raise RuntimeError(f"Items not aligned with the active canonical release: {bad_items[:10]}")


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
    first_release_sha = str(first.get("canonical_release_sha256") or "")
    first_projection_sha = str((first.get("publication") or {}).get("projection_sha256") or "")
    if not first_release_sha or not first_projection_sha:
        raise RuntimeError("First canonical publication returned incomplete release/projection attestation")
    if _current_projection_sha() != first_projection_sha:
        raise RuntimeError("First published DB projection does not match its persisted attestation")
    _assert_structural_contract(first_snapshot, first_release_sha, first_projection_sha)
    first_digest = _digest(first_snapshot)

    second = run_seed_all()
    second_snapshot = _snapshot()
    second_release_sha = str(second.get("canonical_release_sha256") or "")
    second_projection_sha = str((second.get("publication") or {}).get("projection_sha256") or "")
    if first_release_sha != second_release_sha:
        raise RuntimeError(
            "Canonical release digest changed across repeated publication: "
            f"{first_release_sha} != {second_release_sha}"
        )
    if first_projection_sha != second_projection_sha:
        raise RuntimeError(
            "Canonical DB projection digest changed across repeated publication: "
            f"{first_projection_sha} != {second_projection_sha}"
        )
    if _current_projection_sha() != second_projection_sha:
        raise RuntimeError("Second published DB projection does not match its persisted attestation")
    _assert_second_publication_is_noop(second)
    _assert_structural_contract(second_snapshot, second_release_sha, second_projection_sha)
    second_digest = _digest(second_snapshot)

    if first_digest != second_digest:
        sections = [name for name in first_snapshot if first_snapshot[name] != second_snapshot[name]]
        raise RuntimeError(
            "Database content identity changed across repeated canonical publication: "
            f"sections={sections}, first={first_digest}, second={second_digest}"
        )

    print(json.dumps({
        "status": "ok",
        "canonical_release_sha256": second_release_sha,
        "canonical_projection_sha256": second_projection_sha,
        "database_snapshot_sha256": second_digest,
        "items": len(second_snapshot["items"]),
        "steps": len(second_snapshot["steps"]),
        "options": len(second_snapshot["options"]),
        "asset_links": len(second_snapshot["assets"]),
        "skills": len(second_snapshot["skills"]),
        "active_release": VERSION,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
