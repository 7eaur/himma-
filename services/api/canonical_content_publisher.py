"""Publish the final Himma canonical release to PostgreSQL.

The release builder owns academic/current presentation truth and complete media
resolution. This publisher owns persistence and historical safety:
- existing ContentItem and ContentStep IDs are preserved;
- superseded ContentOption rows are retired, never deleted/reinterpreted;
- current media links are replaced from the explicit semantic contract;
- the DB-only runtime snapshot contains no raw source text;
- all writes occur in one transaction after digest/content/media validation.

Legacy baseline/addition seeders may still be used by seed_all as *bootstrap
importers* on an empty database, but no legacy correction/projection seed is part
of the current publication path.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

from canonical_media_guard import assert_media_contract
from canonical_release import assert_question_contract_coverage, build_canonical_release
from content_approval_contract_2026_09_08 import (
    LEARNING_VERSION,
    POSTTEST_VERSION,
    PRETEST_VERSION,
    VERSION,
)
from content_option_lifecycle import set_exact_current_options
from db.database import SessionLocal
from db.models import ContentAssetLink, ContentItem, ContentRelease, ContentStep, Skill

DB_RUNTIME_VERSION = "HIMMA-DB-RUNTIME-2.0"
PUBLISHER_VERSION = "HIMMA-CANONICAL-PUBLISHER-1.0"
ORDER = {"sequence", "memory_sequence", "path_sequence", "build_word"}
READ = {"read_aloud", "timed_read_aloud"}


def _canonical(item: ContentItem) -> str:
    return str((item.template_data or {}).get("canonical_id") or item.stable_key)


def _item_checksum(spec: dict[str, Any]) -> str:
    raw = json.dumps(spec, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _assert_release_digest(release: dict[str, Any]) -> None:
    expected = str(release.get("sha256") or "")
    value = deepcopy(release)
    value.pop("sha256", None)
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    actual = hashlib.sha256(raw).hexdigest()
    if not expected or expected != actual:
        raise RuntimeError(f"Canonical release digest mismatch: expected={expected!r} actual={actual!r}")


def _runtime_interaction(canonical: str) -> str:
    return "read_aloud" if canonical in READ else "multiple_choice"


def _stimulus_text(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    if value.get("kind") == "text":
        return str(value.get("text") or "")
    return ""


def _find_item(db, spec: dict[str, Any]) -> ContentItem:
    stable_key = str(spec["stable_key"])
    direct = db.query(ContentItem).filter(ContentItem.stable_key == stable_key).first()
    if direct is not None:
        return direct
    canonical = str(spec["canonical_id"])
    matches = [item for item in db.query(ContentItem).all() if _canonical(item) == canonical]
    if len(matches) != 1:
        raise RuntimeError(f"Canonical publisher expected one existing item {canonical}, found {len(matches)}")
    return matches[0]


def _reconcile_skills(db, release: dict[str, Any]) -> dict[str, Skill]:
    """Preserve durable skill rows while applying approved semantic replacement."""
    for value in release.get("skill_reconciliations", []):
        level = int(value["level_id"])
        target_code = str(value["to_code"])
        target = db.query(Skill).filter(
            Skill.canonical_skill_id == target_code,
            Skill.level_id == level,
        ).first()
        if target is None:
            target = db.query(Skill).filter(
                Skill.canonical_skill_id == str(value["from_code"]),
                Skill.level_id == level,
            ).first()
        if target is None:
            raise RuntimeError(f"Missing durable skill row for {value['from_code']} -> {target_code}")
        target.canonical_skill_id = target_code
        target.name = str(value["name"])
        target.description = str(value.get("description") or value["name"])
        target.level_id = level

    by_code: dict[str, Skill] = {}
    for skill in db.query(Skill).all():
        code = str(skill.canonical_skill_id or "")
        if code:
            key = f"{int(skill.level_id)}:{code}"
            if key in by_code and by_code[key].id != skill.id:
                raise RuntimeError(f"Duplicate canonical skill rows after reconciliation: {key}")
            by_code[key] = skill
    return by_code


def _replace_assets(db, owner, specs: list[dict[str, Any]]) -> None:
    # ContentAssetLink rows are presentation metadata and are not referenced by
    # historical AttemptResponse rows, so replacing the current links is safe.
    for link in list(owner.assets):
        db.delete(link)
    db.flush()
    for value in specs:
        asset_id = str(value.get("asset_id") or "")
        asset_type = str(value.get("asset_type") or "")
        if not asset_id or not asset_type:
            raise RuntimeError("Canonical media link has no asset_id/asset_type")
        kwargs: dict[str, Any] = {
            "manifest_asset_id": asset_id,
            "asset_type": asset_type,
            "usage_context": str(value.get("usage") or "") or None,
        }
        if isinstance(owner, ContentStep):
            kwargs["step_id"] = owner.id
        else:
            kwargs["item_id"] = owner.id
        db.add(ContentAssetLink(**kwargs))
    db.flush()


def _publish_steps(db, item: ContentItem, spec: dict[str, Any]) -> tuple[int, int, int]:
    compiled = list(spec["rounds"])
    existing = sorted(item.steps, key=lambda value: (int(value.order_index), int(value.id or 0)))
    if len(existing) != len(compiled):
        raise RuntimeError(
            f"{spec['canonical_id']}: publisher refuses to change durable round count "
            f"existing={len(existing)} compiled={len(compiled)}"
        )
    by_order = {int(step.order_index): step for step in existing}
    if len(by_order) != len(existing):
        raise RuntimeError(f"{spec['canonical_id']}: duplicate durable round order")

    created = reactivated = retired = 0
    for round_spec in compiled:
        order = int(round_spec["order_index"])
        step = by_order.get(order)
        if step is None:
            raise RuntimeError(f"{spec['canonical_id']}: missing durable round {order}")
        step.prompt_text = str(round_spec["question_text"])
        expected = round_spec.get("expected_reading_text")
        step.expected_reading_text = str(expected) if expected not in {None, ""} else None
        desired = [
            (str(value["text"]), bool(value.get("is_correct")))
            for value in round_spec.get("options", [])
        ]
        lifecycle = set_exact_current_options(
            db,
            step,
            desired,
            allow_repeated=str(spec["interaction_type"]) in ORDER,
        )
        created += lifecycle["created"]
        reactivated += lifecycle["reactivated"]
        retired += lifecycle["retired"]
        _replace_assets(db, step, list(round_spec.get("media") or []))
    return created, reactivated, retired


def _assessment_projection(item: ContentItem, spec: dict[str, Any], version: str, section: str) -> dict[str, Any]:
    if len(spec["rounds"]) != 1:
        raise RuntimeError(f"{spec['canonical_id']}: assessment item must have one round")
    step = spec["rounds"][0]
    return {
        "version": version,
        "question_number": int(spec["order_index"]),
        "section": section,
        "skill": item.skill.name if item.skill is not None else str(spec["canonical_skill_code"]),
        "encouragement": str(step["encouragement"]),
        "hint": str(step["hint"]),
        "question_text": str(step["question_text"]),
        "instruction_text": str(step["instruction_text"]),
        "interaction_type": str(spec["interaction_type"]),
        "stimulus": deepcopy(step.get("stimulus") or {"kind": "none"}),
    }


def _learning_projection(item: ContentItem, spec: dict[str, Any]) -> dict[str, Any]:
    skill = item.skill.name if item.skill is not None else str(spec["canonical_skill_code"])
    rounds = []
    for step in spec["rounds"]:
        rounds.append({
            "round_number": int(step["order_index"]),
            "round_total": len(spec["rounds"]),
            "skill": skill,
            "encouragement": str(step["encouragement"]),
            "hint": str(step["hint"]),
            "question_text": str(step["question_text"]),
            "instruction_text": str(step["instruction_text"]),
            "stimulus_text": _stimulus_text(step.get("stimulus")),
            "stimulus": deepcopy(step.get("stimulus") or {"kind": "none"}),
        })
    return {
        "version": LEARNING_VERSION,
        "projection_contract": "canonical_release_v3",
        "rounds": rounds,
    }


def _runtime_snapshot(spec: dict[str, Any], release_sha: str) -> dict[str, Any]:
    return {
        "version": DB_RUNTIME_VERSION,
        "canonical_release_version": VERSION,
        "canonical_release_sha256": release_sha,
        "rounds": [
            {
                "order_index": int(step["order_index"]),
                "assets": deepcopy(step.get("media") or []),
                "media_gaps": deepcopy(step.get("media_gaps") or []),
            }
            for step in spec["rounds"]
        ],
        "item_assets": deepcopy(spec.get("item_assets") or []),
    }


def _publish_item(db, item: ContentItem, spec: dict[str, Any], skill_map: dict[str, Skill], release_sha: str) -> dict[str, int]:
    canonical = str(spec["canonical_id"])
    skill_key = f"{int(spec['level_id'])}:{str(spec['canonical_skill_code'])}"
    skill = skill_map.get(skill_key)
    if skill is None:
        raise RuntimeError(f"{canonical}: missing canonical skill {skill_key}")

    item.kind = str(spec["kind"])
    item.level_id = int(spec["level_id"])
    item.skill_id = int(skill.id)
    item.interaction_type = _runtime_interaction(str(spec["interaction_type"]))
    item.order_index = int(spec["order_index"])
    item.status = "approved"
    item.checksum = _item_checksum(spec)

    created, reactivated, retired = _publish_steps(db, item, spec)
    _replace_assets(db, item, list(spec.get("item_assets") or []))

    # Refresh relationships used while constructing the student projection.
    item.skill = skill
    data = dict(item.template_data or {})
    data.update({
        "canonical_id": canonical,
        "title": str(spec["title"]),
        "canonical_interaction_type": str(spec["interaction_type"]),
        "criterion": spec.get("criterion"),
        "canonical_release_version": VERSION,
        "canonical_release_sha256": release_sha,
        "canonical_publisher_version": PUBLISHER_VERSION,
        "db_runtime": _runtime_snapshot(spec, release_sha),
        "item_assets": deepcopy(spec.get("item_assets") or []),
    })
    approval = {
        "version": VERSION,
        "source": "HIMMA_CONTENT_APPROVAL_MASTER_INDEX_2026-09-08_AR.md",
    }
    if spec.get("context_intro"):
        approval["context_intro"] = deepcopy(spec["context_intro"])
    if spec.get("layout_hint"):
        approval["layout_hint"] = str(spec["layout_hint"])
    data["content_approval_2026_09_08"] = approval

    if item.kind == "pretest_question":
        data["pretest_experience_version"] = PRETEST_VERSION
        data["pretest_experience"] = _assessment_projection(item, spec, PRETEST_VERSION, "الاختبار القبلي")
    elif item.kind == "posttest_question":
        data["posttest_experience_version"] = POSTTEST_VERSION
        data["posttest_experience"] = _assessment_projection(item, spec, POSTTEST_VERSION, "الاختبار البعدي")
    elif item.kind in {"core_activity", "reinforcement_activity"}:
        data["learning_experience_version"] = LEARNING_VERSION
        data["learning_experience"] = _learning_projection(item, spec)
    item.template_data = data
    return {"created": created, "reactivated": reactivated, "retired": retired}


def _activate_release(db, release: dict[str, Any]) -> None:
    for row in db.query(ContentRelease).all():
        row.is_active = False
    current = db.query(ContentRelease).filter(ContentRelease.version == str(release["release_version"])).first()
    if current is None:
        current = ContentRelease(version=str(release["release_version"]), is_active=True)
        db.add(current)
    else:
        current.is_active = True


def publish_release(release: dict[str, Any] | None = None) -> dict[str, Any]:
    canonical = release or build_canonical_release()
    if str(canonical.get("release_version")) != VERSION:
        raise RuntimeError("Publisher received the wrong canonical release version")
    items = list(canonical.get("items") or [])
    if len(items) != 125:
        raise RuntimeError(f"Publisher requires the validated 125-item release, got {len(items)}")

    # Never let a caller bypass the canonical builder with a stale/tampered
    # object. Publication is fail-closed before a database transaction begins.
    _assert_release_digest(canonical)
    assert_question_contract_coverage(canonical)
    assert_media_contract(canonical)

    db = SessionLocal()
    try:
        existing_count = db.query(ContentItem).count()
        if existing_count != 125:
            raise RuntimeError(
                "Canonical publisher expects the structural 125-item bootstrap to exist; "
                f"found {existing_count}. Run seed_all so import-only bootstrap can create it first."
            )
        skills = _reconcile_skills(db, canonical)
        totals = {"created": 0, "reactivated": 0, "retired": 0}
        published_ids: set[int] = set()
        for spec in items:
            item = _find_item(db, spec)
            if int(item.id) in published_ids:
                raise RuntimeError(f"Two canonical specs resolved to the same durable ContentItem id={item.id}")
            published_ids.add(int(item.id))
            result = _publish_item(db, item, spec, skills, str(canonical["sha256"]))
            for key in totals:
                totals[key] += int(result[key])
        if len(published_ids) != 125:
            raise RuntimeError("Canonical publisher did not resolve 125 unique durable item rows")
        _activate_release(db, canonical)
        db.commit()
        return {
            "release_version": str(canonical["release_version"]),
            "release_sha256": str(canonical["sha256"]),
            "items": len(published_ids),
            "option_rows_created": totals["created"],
            "option_rows_reactivated": totals["reactivated"],
            "option_rows_retired": totals["retired"],
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print(publish_release())
