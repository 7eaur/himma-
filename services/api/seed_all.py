"""Build and publish the complete current Himma content release.

There is one execution path only:
1. build and validate the DB-free canonical 125-item release;
2. publish/bootstrap it transactionally through ``canonical_content_publisher``;
3. verify the exact current DB projection counts and version markers.

Legacy catalog/addition files are compile-time migration inputs used by the
canonical compiler. Their historical seed modules are NOT executed here and no
correction/projection repair chain runs after publication.
"""
from __future__ import annotations

import json
from pathlib import Path

from canonical_content_publisher import DB_RUNTIME_VERSION, publish_release
from canonical_release import build_canonical_release
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
    values = {str(item["stable_key"]) for item in payload["items"]}
    if len(values) != 105:
        raise RuntimeError(f"Historical baseline identity must contain 105 stable keys, got {len(values)}")
    return values


def run_seed_all() -> dict[str, object]:
    # Validation/media resolution happens before publisher opens its transaction.
    # The publisher can create missing structure itself, so a failed canonical
    # release never leaves a partially committed legacy bootstrap behind.
    release = build_canonical_release()
    publication = publish_release(release)

    db = SessionLocal()
    try:
        all_items = db.query(ContentItem).all()
        total = len(all_items)
        base_count = db.query(ContentItem).filter(ContentItem.stable_key.in_(_base_stable_keys())).count()
        pretest_count = db.query(ContentItem).filter(ContentItem.kind == "pretest_question").count()
        posttest_count = db.query(ContentItem).filter(ContentItem.kind == "posttest_question").count()
        core_count = db.query(ContentItem).filter(ContentItem.kind == "core_activity").count()
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
    actual_kinds = {
        "pretest": int(pretest_count),
        "posttest": int(posttest_count),
        "core": int(core_count),
        "reinforcement": int(reinforcement_count),
    }
    expected_kinds = {"pretest": 30, "posttest": 30, "core": 30, "reinforcement": 35}
    if actual_kinds != expected_kinds:
        raise RuntimeError(f"Canonical runtime kind counts mismatch: {actual_kinds}")
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

    v1_created = int(publication.get("v1_rows_created") or 0)
    v2_created = int(publication.get("v2_rows_created") or 0)
    result: dict[str, object] = {
        "baseline_items": int(base_count),
        # Keep the long-standing public/test count keys while the canonical
        # markers below prove the same projection at the current version.
        "pretest_items": int(pretest_count),
        "posttest_items": int(posttest_count),
        "core_items": int(core_count),
        "reinforcement_items": int(reinforcement_count),
        "total_items": int(total),
        "v1_additions_created": v1_created,
        "v2_additions_created": v2_created,
        "additions_created": v1_created + v2_created,
        "canonical_release_version": VERSION,
        "canonical_release_sha256": release["sha256"],
        "canonical_release_items": release_marked,
        "db_runtime_items": db_runtime_marked,
        "pretest_experience_items": pretest_marked,
        "learning_experience_items": learning_marked,
        "posttest_experience_items": posttest_marked,
        "publication": publication,
    }
    print(f"Himma canonical content publication OK: {result}")
    return result


if __name__ == "__main__":
    run_seed_all()
