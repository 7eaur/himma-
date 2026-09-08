"""Build and publish the complete current Himma content release.

Only two legacy seed families remain here, and only as structural bootstrap
importers for an empty/old database:
- seed.py creates the durable 105 client-catalog item/step/skill rows + scoring;
- reinforcement addition importers create the 20 durable extension rows.

They are never the final content source. Once the structural 125 rows exist, the
DB-free canonical compiler creates one validated release and the transactional
publisher replaces the *current* option/media/presentation contract while
preserving historical item/step/option evidence.

The retired correction/projection chain is intentionally NOT called here.
"""
from __future__ import annotations

import json
from pathlib import Path

import seed
import seed_reinforcement_additions
import seed_reinforcement_additions_v2
from canonical_content_compiler import compile_release
from canonical_content_publisher import DB_RUNTIME_VERSION, publish_release
from content_approval_contract_2026_09_08 import (
    LEARNING_VERSION,
    POSTTEST_VERSION,
    PRETEST_VERSION,
    VERSION,
)
from db.database import SessionLocal
from db.models import ContentItem

ROOT = Path(__file__).resolve().parents[2]
BASE_CATALOG = ROOT / "packages" / "content" / "src" / "catalog.json"


def _base_stable_keys() -> set[str]:
    payload = json.loads(BASE_CATALOG.read_text(encoding="utf-8"))
    return {str(item["stable_key"]) for item in payload["items"]}


def _counts() -> tuple[int, int]:
    db = SessionLocal()
    try:
        base = db.query(ContentItem).filter(ContentItem.stable_key.in_(_base_stable_keys())).count()
        total = db.query(ContentItem).count()
        return int(base), int(total)
    finally:
        db.close()


def _bootstrap_structure() -> tuple[int, int]:
    """Create missing durable rows only; never re-run importers after publication."""
    base_count, total = _counts()
    if base_count < 105:
        seed.run_seed()
        base_count, total = _counts()
    if base_count != 105:
        raise RuntimeError(f"Expected 105 durable baseline rows after bootstrap, got {base_count}")

    v1_created = v2_created = 0
    if total < 125:
        v1_created = seed_reinforcement_additions.run_seed()
        v2_created = seed_reinforcement_additions_v2.run_seed()
        _, total = _counts()
    if total != 125:
        raise RuntimeError(f"Expected exactly 125 durable content rows before canonical publish, got {total}")
    return int(v1_created), int(v2_created)


def run_seed_all() -> dict[str, object]:
    v1_created, v2_created = _bootstrap_structure()

    release = compile_release()
    publication = publish_release(release)

    db = SessionLocal()
    try:
        all_items = db.query(ContentItem).all()
        total = len(all_items)
        base_count = db.query(ContentItem).filter(ContentItem.stable_key.in_(_base_stable_keys())).count()
        reinforcement_count = db.query(ContentItem).filter(ContentItem.kind == "reinforcement_activity").count()
        release_marked = sum(
            1 for item in all_items
            if (item.template_data or {}).get("canonical_release_version") == VERSION
            and (item.template_data or {}).get("canonical_release_sha256") == release["sha256"]
        )
        db_runtime_marked = sum(
            1 for item in all_items
            if ((item.template_data or {}).get("db_runtime") or {}).get("version") == DB_RUNTIME_VERSION
        )
        pretest_marked = sum(
            1 for item in all_items
            if item.kind == "pretest_question"
            and (item.template_data or {}).get("pretest_experience_version") == PRETEST_VERSION
        )
        learning_marked = sum(
            1 for item in all_items
            if item.kind in {"core_activity", "reinforcement_activity"}
            and (item.template_data or {}).get("learning_experience_version") == LEARNING_VERSION
        )
        posttest_marked = sum(
            1 for item in all_items
            if item.kind == "posttest_question"
            and (item.template_data or {}).get("posttest_experience_version") == POSTTEST_VERSION
        )
    finally:
        db.close()

    if base_count != 105:
        raise RuntimeError(f"Expected 105 baseline items, got {base_count}")
    if reinforcement_count != 35:
        raise RuntimeError(f"Expected 35 reinforcement items, got {reinforcement_count}")
    if total != 125:
        raise RuntimeError(f"Expected 125 total runtime items, got {total}")
    if release_marked != 125:
        raise RuntimeError(f"Expected canonical release on 125 items, got {release_marked}")
    if db_runtime_marked != 125:
        raise RuntimeError(f"Expected {DB_RUNTIME_VERSION} on 125 items, got {db_runtime_marked}")
    if pretest_marked != 30:
        raise RuntimeError(f"Expected {PRETEST_VERSION} on 30 pretest items, got {pretest_marked}")
    if learning_marked != 65:
        raise RuntimeError(f"Expected {LEARNING_VERSION} on 65 learning items, got {learning_marked}")
    if posttest_marked != 30:
        raise RuntimeError(f"Expected {POSTTEST_VERSION} on 30 posttest items, got {posttest_marked}")

    result: dict[str, object] = {
        "baseline_items":base_count,
        "reinforcement_items":reinforcement_count,
        "total_items":total,
        "v1_additions_created":v1_created,
        "v2_additions_created":v2_created,
        "additions_created":v1_created + v2_created,
        "canonical_release_version":VERSION,
        "canonical_release_sha256":release["sha256"],
        "canonical_release_items":release_marked,
        "db_runtime_items":db_runtime_marked,
        "pretest_experience_items":pretest_marked,
        "learning_experience_items":learning_marked,
        "posttest_experience_items":posttest_marked,
        "publication":publication,
    }
    print(f"Himma canonical content publication OK: {result}")
    return result


if __name__ == "__main__":
    run_seed_all()
