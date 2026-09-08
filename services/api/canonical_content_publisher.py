"""Publish the final Himma canonical release to PostgreSQL.

The release builder owns academic/current presentation truth and complete media
resolution. This publisher owns persistence and historical safety:
- a fresh database is bootstrapped directly from the validated canonical release;
- existing ContentItem and ContentStep IDs are preserved;
- superseded ContentOption rows are retired, never deleted/reinterpreted;
- current media links are reconciled from the explicit semantic contract;
- unchanged media links keep their durable IDs across repeated publication;
- the DB-only runtime snapshot contains no raw source text;
- the final current DB projection receives an independent semantic digest;
- structural bootstrap, current publication, scoring rows and release activation
  happen in ONE transaction after release/content/media validation.

Legacy seed modules are no longer required on the publication path. Historical
catalog files remain compile-time migration inputs in ``canonical_release`` only;
student runtime never parses them and no post-publication repair seed exists.
"""
from __future__ import annotations

import datetime
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
from content_projection_digest import projection_sha256
from db.database import SessionLocal
from db.models import (
    ContentAssetLink,
    ContentItem,
    ContentRelease,
    ContentStep,
    ScoringPolicy,
    ScoringRule,
    Skill,
)

DB_RUNTIME_VERSION = "HIMMA-DB-RUNTIME-2.0"
PUBLISHER_VERSION = "HIMMA-CANONICAL-PUBLISHER-2.0"
ORDER = {"sequence", "memory_sequence", "path_sequence", "build_word"}
READ = {"read_aloud", "timed_read_aloud"}
BASE_SOURCE = "client_catalog_105"
BASE_VERSION = "HIMMA-CONTENT-1.0"
REINFORCEMENT_V1 = "HIMMA-REINFORCEMENT-ADD-1.0"
REINFORCEMENT_V2 = "HIMMA-REINFORCEMENT-ADD-2.0"
SCORING_POLICY_VERSION = "SCORING_POLICY_V1"


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


def _assert_exact_canonical_identity(release: dict[str, Any]) -> None:
    """Reject caller-supplied variants even if they were re-hashed correctly."""
    expected = build_canonical_release()
    actual_sha = str(release.get("sha256") or "")
    expected_sha = str(expected.get("sha256") or "")
    if actual_sha != expected_sha:
        raise RuntimeError(
            "Publisher only accepts the exact release produced by build_canonical_release: "
            f"expected={expected_sha!r} actual={actual_sha!r}"
        )


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


def _expected_skill_keys(release: dict[str, Any]) -> set[str]:
    result = {
        f"{int(value['level_id'])}:{str(value['skill_code'])}"
        for value in release.get("skills", [])
    }
    for value in release.get("skill_reconciliations", []):
        result.discard(f"{int(value['level_id'])}:{str(value['from_code'])}")
        result.add(f"{int(value['level_id'])}:{str(value['to_code'])}")
    return result


def _ensure_skills(db, release: dict[str, Any]) -> dict[str, Skill]:
    """Create only missing durable skill rows, then apply semantic reconciliation."""
    source_skills = list(release.get("skills") or [])
    if len(source_skills) != 44:
        raise RuntimeError(f"Canonical release must carry 44 source skill rows, got {len(source_skills)}")

    source_keys = {str(value["skill_id"]) for value in source_skills}
    if len(source_keys) != len(source_skills):
        raise RuntimeError("Canonical release contains duplicate skill_id values")

    existing = {str(skill.skill_key): skill for skill in db.query(Skill).all()}
    unexpected_keys = sorted(set(existing) - source_keys)
    if unexpected_keys:
        raise RuntimeError(f"Database contains non-canonical skill rows: {unexpected_keys}")

    for value in source_skills:
        skill_key = str(value["skill_id"])
        skill = existing.get(skill_key)
        if skill is None:
            skill = Skill(
                skill_key=skill_key,
                canonical_skill_id=str(value["skill_code"]),
                name=str(value["name"]),
                description=str(value["name"]),
                level_id=int(value["level_id"]),
            )
            db.add(skill)
            existing[skill_key] = skill
        else:
            # These are the immutable source semantics. A newer approved semantic
            # replacement is applied immediately below in the same transaction.
            skill.canonical_skill_id = str(value["skill_code"])
            skill.name = str(value["name"])
            skill.description = str(value["name"])
            skill.level_id = int(value["level_id"])
    db.flush()

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
    db.flush()

    by_code: dict[str, Skill] = {}
    for skill in db.query(Skill).all():
        code = str(skill.canonical_skill_id or "")
        if not code:
            raise RuntimeError(f"Skill row {skill.skill_key!r} has no canonical_skill_id")
        key = f"{int(skill.level_id)}:{code}"
        if key in by_code and by_code[key].id != skill.id:
            raise RuntimeError(f"Duplicate canonical skill rows after reconciliation: {key}")
        by_code[key] = skill

    expected = _expected_skill_keys(release)
    if set(by_code) != expected:
        raise RuntimeError(
            "Canonical skill projection mismatch after reconciliation: "
            f"missing={sorted(expected - set(by_code))} extra={sorted(set(by_code) - expected)}"
        )
    return by_code


def _source_version(spec: dict[str, Any]) -> str:
    source = str(spec.get("source_release") or "")
    if source == BASE_SOURCE:
        return BASE_VERSION
    if source in {REINFORCEMENT_V1, REINFORCEMENT_V2}:
        return source
    raise RuntimeError(f"{spec['canonical_id']}: unsupported structural source release {source!r}")


def _ensure_item_structures(
    db,
    release: dict[str, Any],
    skills: dict[str, Skill],
) -> dict[str, int]:
    """Create only missing item/step structure inside the publication transaction.

    Existing rows are never replaced, so attempts and historical option IDs keep
    their durable foreign-key targets. New rows are created from the already
    validated canonical release rather than from a legacy seeder that can commit
    partial state before the final publication succeeds.
    """
    specs = list(release.get("items") or [])
    expected_stable = {str(spec["stable_key"]) for spec in specs}
    expected_canonical = {str(spec["canonical_id"]) for spec in specs}
    if len(expected_stable) != 125 or len(expected_canonical) != 125:
        raise RuntimeError("Canonical release structural identity is not exactly 125 unique items")

    created = {"baseline": 0, "v1": 0, "v2": 0}
    resolved_ids: set[int] = set()

    for spec in specs:
        stable_key = str(spec["stable_key"])
        canonical = str(spec["canonical_id"])
        item = db.query(ContentItem).filter(ContentItem.stable_key == stable_key).first()
        if item is None:
            canonical_matches = [row for row in db.query(ContentItem).all() if _canonical(row) == canonical]
            if len(canonical_matches) > 1:
                raise RuntimeError(f"{canonical}: multiple durable rows exist before publication")
            item = canonical_matches[0] if canonical_matches else None

        if item is None:
            skill_key = f"{int(spec['level_id'])}:{str(spec['canonical_skill_code'])}"
            skill = skills.get(skill_key)
            if skill is None:
                raise RuntimeError(f"{canonical}: missing skill {skill_key} during structural bootstrap")
            item = ContentItem(
                stable_key=stable_key,
                kind=str(spec["kind"]),
                level_id=int(spec["level_id"]),
                skill_id=int(skill.id),
                interaction_type=_runtime_interaction(str(spec["interaction_type"])),
                order_index=int(spec["order_index"]),
                version=_source_version(spec),
                status="draft",
                checksum=_item_checksum(spec),
                template_data={
                    "canonical_id": canonical,
                    "title": str(spec["title"]),
                },
            )
            db.add(item)
            db.flush()
            for round_spec in spec["rounds"]:
                expected = round_spec.get("expected_reading_text")
                db.add(ContentStep(
                    item_id=int(item.id),
                    order_index=int(round_spec["order_index"]),
                    prompt_text=str(round_spec["question_text"]),
                    expected_reading_text=str(expected) if expected not in {None, ""} else None,
                ))
            db.flush()
            source = str(spec.get("source_release") or "")
            if source == BASE_SOURCE:
                created["baseline"] += 1
            elif source == REINFORCEMENT_V1:
                created["v1"] += 1
            elif source == REINFORCEMENT_V2:
                created["v2"] += 1
        else:
            # Stable identity is immutable. A canonical-ID fallback is accepted
            # only when it resolves the same logical row; rewriting stable_key on
            # an existing item would be a separate reviewed migration.
            if str(item.stable_key) != stable_key:
                raise RuntimeError(
                    f"{canonical}: existing stable_key {item.stable_key!r} differs from canonical {stable_key!r}"
                )
            if len(item.steps) != len(spec["rounds"]):
                raise RuntimeError(
                    f"{canonical}: durable round count differs from canonical release "
                    f"existing={len(item.steps)} canonical={len(spec['rounds'])}"
                )

        if int(item.id) in resolved_ids:
            raise RuntimeError(f"Two canonical specs resolved to ContentItem id={item.id}")
        resolved_ids.add(int(item.id))

    db.flush()
    all_rows = db.query(ContentItem).all()
    actual_stable = {str(item.stable_key) for item in all_rows}
    actual_canonical = {_canonical(item) for item in all_rows}
    if len(all_rows) != 125 or actual_stable != expected_stable or actual_canonical != expected_canonical:
        raise RuntimeError(
            "Database content structure is not the exact canonical 125-item set: "
            f"count={len(all_rows)} "
            f"missing_stable={sorted(expected_stable - actual_stable)} "
            f"extra_stable={sorted(actual_stable - expected_stable)} "
            f"missing_canonical={sorted(expected_canonical - actual_canonical)} "
            f"extra_canonical={sorted(actual_canonical - expected_canonical)}"
        )
    return created


def _asset_key(asset_id: str, asset_type: str, usage: str | None) -> tuple[str, str, str | None]:
    return (asset_id, asset_type, usage or None)


def _reconcile_assets(db, owner, specs: list[dict[str, Any]]) -> tuple[int, int]:
    """Reconcile current media links without churn on repeated publication.

    ``db_runtime`` owns the semantic text and option-order relationship. The
    relational link only proves that the asset is currently attached to the item
    or step, so its durable identity is keyed by asset/type/usage. Duplicate keys
    are treated as a multiset to avoid silently dropping intentional repeats.
    """
    desired: list[tuple[str, str, str | None]] = []
    for value in specs:
        asset_id = str(value.get("asset_id") or "").strip()
        asset_type = str(value.get("asset_type") or "").strip()
        usage = str(value.get("usage") or "").strip() or None
        if not asset_id or not asset_type:
            raise RuntimeError("Canonical media link has no asset_id/asset_type")
        desired.append(_asset_key(asset_id, asset_type, usage))

    available: dict[tuple[str, str, str | None], list[ContentAssetLink]] = {}
    for link in list(owner.assets):
        key = _asset_key(
            str(link.manifest_asset_id or ""),
            str(link.asset_type or ""),
            str(link.usage_context) if link.usage_context else None,
        )
        available.setdefault(key, []).append(link)

    created = 0
    for asset_id, asset_type, usage in desired:
        key = _asset_key(asset_id, asset_type, usage)
        bucket = available.get(key) or []
        if bucket:
            bucket.pop()
            continue
        kwargs: dict[str, Any] = {
            "manifest_asset_id": asset_id,
            "asset_type": asset_type,
            "usage_context": usage,
        }
        if isinstance(owner, ContentStep):
            kwargs["step_id"] = owner.id
        else:
            kwargs["item_id"] = owner.id
        db.add(ContentAssetLink(**kwargs))
        created += 1

    stale = [link for bucket in available.values() for link in bucket]
    for link in stale:
        db.delete(link)

    if created or stale:
        db.flush()
    return created, len(stale)


def _publish_steps(db, item: ContentItem, spec: dict[str, Any]) -> dict[str, int]:
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

    totals = {
        "option_created": 0,
        "option_reactivated": 0,
        "option_retired": 0,
        "asset_created": 0,
        "asset_retired": 0,
    }
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
        totals["option_created"] += int(lifecycle["created"])
        totals["option_reactivated"] += int(lifecycle["reactivated"])
        totals["option_retired"] += int(lifecycle["retired"])
        asset_created, asset_retired = _reconcile_assets(db, step, list(round_spec.get("media") or []))
        totals["asset_created"] += asset_created
        totals["asset_retired"] += asset_retired
    return totals


def _assessment_projection(item: ContentItem, spec: dict[str, Any], version: str, section: str) -> dict[str, Any]:
    if len(spec["rounds"]) != 1:
        raise RuntimeError(f"{spec['canonical_id']}: assessment item must have one round")
    step = spec["rounds"][0]
    default_skill = item.skill.name if item.skill is not None else str(spec["canonical_skill_code"])
    return {
        "version": version,
        "question_number": int(spec["order_index"]),
        "section": section,
        "skill": str(spec.get("presentation_skill") or default_skill),
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

    totals = _publish_steps(db, item, spec)
    asset_created, asset_retired = _reconcile_assets(db, item, list(spec.get("item_assets") or []))
    totals["asset_created"] += asset_created
    totals["asset_retired"] += asset_retired

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
    return totals


def _ensure_scoring_policy(db) -> int:
    """Ensure one historical-compatible scoring rule per assessment item."""
    policy = db.query(ScoringPolicy).filter(ScoringPolicy.version == SCORING_POLICY_VERSION).first()
    if policy is None:
        policy = ScoringPolicy(
            version=SCORING_POLICY_VERSION,
            status="approved",
            approved_by=None,
            approved_at=datetime.datetime(2026, 8, 11, tzinfo=datetime.timezone.utc),
            checksum="seeded_by_canonical_publisher",
        )
        db.add(policy)
        db.flush()

    created = 0
    assessment_items = db.query(ContentItem).filter(
        ContentItem.kind.in_(("pretest_question", "posttest_question"))
    ).all()
    if len(assessment_items) != 60:
        raise RuntimeError(f"Canonical scoring policy expects 60 assessment items, got {len(assessment_items)}")

    for item in assessment_items:
        rules = db.query(ScoringRule).filter(
            ScoringRule.policy_id == policy.id,
            ScoringRule.item_id == item.id,
        ).all()
        if len(rules) > 1:
            raise RuntimeError(f"Duplicate scoring rules for assessment item {item.id}")
        if not rules:
            db.add(ScoringRule(
                policy_id=int(policy.id),
                item_id=int(item.id),
                max_raw_score=1.0,
                rubric=(
                    "V1: 1 point for correct non-audio. For audio: "
                    "max(0, 1 - (errors/target_units))."
                ),
            ))
            created += 1
    return created


def _activate_release(db, release: dict[str, Any]) -> None:
    for row in db.query(ContentRelease).all():
        row.is_active = False
    current = db.query(ContentRelease).filter(ContentRelease.version == str(release["release_version"])).first()
    if current is None:
        current = ContentRelease(version=str(release["release_version"]), is_active=True)
        db.add(current)
    else:
        current.is_active = True


def _stamp_projection_digest(db) -> str:
    """Attest the exact current DB learner projection before the transaction commits."""
    db.flush()
    db.expire_all()
    digest = projection_sha256(db)
    for item in db.query(ContentItem).all():
        data = dict(item.template_data or {})
        data["canonical_projection_sha256"] = digest
        item.template_data = data
    db.flush()
    db.expire_all()
    verified = projection_sha256(db)
    if verified != digest:
        raise RuntimeError(
            "Canonical DB projection changed while being attested: "
            f"expected={digest!r} actual={verified!r}"
        )
    return digest


def publish_release(release: dict[str, Any] | None = None) -> dict[str, Any]:
    canonical = release or build_canonical_release()
    if str(canonical.get("release_version")) != VERSION:
        raise RuntimeError("Publisher received the wrong canonical release version")
    items = list(canonical.get("items") or [])
    if len(items) != 125:
        raise RuntimeError(f"Publisher requires the validated 125-item release, got {len(items)}")

    # No database row is touched until the exact release, complete media package
    # and digest have already passed. The same transaction then owns bootstrap,
    # current content projection, scoring compatibility and release activation.
    _assert_release_digest(canonical)
    assert_question_contract_coverage(canonical)
    assert_media_contract(canonical)
    _assert_exact_canonical_identity(canonical)

    db = SessionLocal()
    try:
        skills = _ensure_skills(db, canonical)
        structure_created = _ensure_item_structures(db, canonical, skills)
        totals = {
            "option_created": 0,
            "option_reactivated": 0,
            "option_retired": 0,
            "asset_created": 0,
            "asset_retired": 0,
        }
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

        scoring_rules_created = _ensure_scoring_policy(db)
        _activate_release(db, canonical)
        projection_digest = _stamp_projection_digest(db)
        db.commit()
        return {
            "release_version": str(canonical["release_version"]),
            "release_sha256": str(canonical["sha256"]),
            "projection_sha256": projection_digest,
            "items": len(published_ids),
            "baseline_rows_created": int(structure_created["baseline"]),
            "v1_rows_created": int(structure_created["v1"]),
            "v2_rows_created": int(structure_created["v2"]),
            "scoring_rules_created": int(scoring_rules_created),
            "option_rows_created": totals["option_created"],
            "option_rows_reactivated": totals["option_reactivated"],
            "option_rows_retired": totals["option_retired"],
            "asset_rows_created": totals["asset_created"],
            "asset_rows_retired": totals["asset_retired"],
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print(publish_release())
