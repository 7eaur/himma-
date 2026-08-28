"""Seed the complete currently approved Himma runtime content set.

Use this entrypoint for fresh/repeatable environments after M03. It preserves
`seed.py` as the immutable 105-item baseline seeder while adding the accepted
v1 maintenance extension and the explicitly approved 2026-08-29 v2 gap release
without causing the baseline legacy guard to misclassify versioned additions.
"""

from __future__ import annotations

import json
from pathlib import Path

import seed
import seed_reinforcement_additions
import seed_reinforcement_additions_v2
from db.database import SessionLocal
from db.models import ContentItem


ROOT = Path(__file__).resolve().parents[2]
BASE_CATALOG = ROOT / "packages" / "content" / "src" / "catalog.json"


def _base_stable_keys() -> set[str]:
    payload = json.loads(BASE_CATALOG.read_text(encoding="utf-8"))
    return {str(item["stable_key"]) for item in payload["items"]}


def _base_is_complete() -> bool:
    required = _base_stable_keys()
    db = SessionLocal()
    try:
        present = {
            row[0]
            for row in db.query(ContentItem.stable_key).filter(
                ContentItem.stable_key.in_(required)
            ).all()
        }
        return required == present
    finally:
        db.close()


def run_seed_all() -> dict[str, int]:
    if not _base_is_complete():
        seed.run_seed()

    v1_created = seed_reinforcement_additions.run_seed()
    v2_created = seed_reinforcement_additions_v2.run_seed()

    db = SessionLocal()
    try:
        total = db.query(ContentItem).count()
        base_count = db.query(ContentItem).filter(
            ContentItem.stable_key.in_(_base_stable_keys())
        ).count()
        reinforcement_count = db.query(ContentItem).filter(
            ContentItem.kind == "reinforcement_activity"
        ).count()
    finally:
        db.close()

    if base_count != 105:
        raise RuntimeError(f"Expected 105 baseline items, got {base_count}")
    if reinforcement_count != 35:
        raise RuntimeError(f"Expected 35 approved reinforcement items, got {reinforcement_count}")
    if total != 125:
        raise RuntimeError(f"Expected 125 total approved runtime items, got {total}")

    result = {
        "baseline_items": base_count,
        "reinforcement_items": reinforcement_count,
        "total_items": total,
        "v1_additions_created": v1_created,
        "v2_additions_created": v2_created,
        "additions_created": v1_created + v2_created,
    }
    print(f"Himma full content seed OK: {result}")
    return result


if __name__ == "__main__":
    run_seed_all()
