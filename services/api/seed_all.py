"""Seed the complete currently approved Himma runtime content set.

Use this entrypoint for fresh/repeatable environments after M03.  It preserves
`seed.py` as the immutable 105-item baseline seeder while adding the approved
18-item reinforcement extension without causing the baseline legacy guard to
misclassify versioned additions on subsequent runs.
"""

from __future__ import annotations

import json
from pathlib import Path

import seed
import seed_reinforcement_additions
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
    # On a fresh/partial database, seed the immutable baseline first.  On a
    # database that already contains the full baseline plus extension rows,
    # avoid rerunning the legacy-mixing guard in seed.py.
    if not _base_is_complete():
        seed.run_seed()

    additions_created = seed_reinforcement_additions.run_seed()

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
    if reinforcement_count != 33:
        raise RuntimeError(f"Expected 33 approved reinforcement items, got {reinforcement_count}")
    if total != 123:
        raise RuntimeError(f"Expected 123 total approved runtime items, got {total}")

    result = {
        "baseline_items": base_count,
        "reinforcement_items": reinforcement_count,
        "total_items": total,
        "additions_created": additions_created,
    }
    print(f"Himma full content seed OK: {result}")
    return result


if __name__ == "__main__":
    run_seed_all()
