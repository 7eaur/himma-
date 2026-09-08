"""Deterministic digest of the *current* DB-backed student content projection.

The canonical release SHA proves which approved source release was published. This
module adds a second, independent attestation over what PostgreSQL currently
contains and what the student runtime can consume. Historical inactive option
rows are intentionally excluded: they remain durable evidence for old responses,
but are not part of the current learner presentation.

The payload is assembled with bulk queries so `/ready` can verify 125 items
without parsing repository source files or performing positional/media inference.
"""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from typing import Any

from db.models import ContentAssetLink, ContentItem, ContentOption, ContentStep, Skill

_CURRENT_TEMPLATE_KEYS = (
    "canonical_id",
    "title",
    "canonical_interaction_type",
    "criterion",
    "canonical_release_version",
    "canonical_release_sha256",
    "canonical_publisher_version",
    "db_runtime",
    "content_approval_2026_09_08",
    "pretest_experience_version",
    "pretest_experience",
    "learning_experience_version",
    "learning_experience",
    "posttest_experience_version",
    "posttest_experience",
)


def _canonical_template(template: dict[str, Any]) -> dict[str, Any]:
    return {
        key: template[key]
        for key in _CURRENT_TEMPLATE_KEYS
        if key in template
    }


def projection_payload(db) -> dict[str, Any]:
    """Return a normalized semantic snapshot of the current learner projection."""
    items = list(db.query(ContentItem).all())
    steps = list(db.query(ContentStep).all())
    options = list(
        db.query(ContentOption)
        .filter(ContentOption.is_active.is_(True))
        .all()
    )
    assets = list(db.query(ContentAssetLink).all())
    skills = {int(skill.id): skill for skill in db.query(Skill).all()}

    steps_by_item: dict[int, list[ContentStep]] = defaultdict(list)
    for step in steps:
        steps_by_item[int(step.item_id)].append(step)

    options_by_step: dict[int, list[ContentOption]] = defaultdict(list)
    for option in options:
        options_by_step[int(option.step_id)].append(option)

    step_assets: dict[int, list[ContentAssetLink]] = defaultdict(list)
    item_assets: dict[int, list[ContentAssetLink]] = defaultdict(list)
    for asset in assets:
        if asset.step_id is not None:
            step_assets[int(asset.step_id)].append(asset)
        elif asset.item_id is not None:
            item_assets[int(asset.item_id)].append(asset)

    normalized_items: list[dict[str, Any]] = []
    for item in items:
        template = dict(item.template_data or {})
        canonical = str(template.get("canonical_id") or item.stable_key)
        skill = skills.get(int(item.skill_id))
        rounds: list[dict[str, Any]] = []
        for step in sorted(
            steps_by_item.get(int(item.id), []),
            key=lambda value: (int(value.order_index), int(value.id or 0)),
        ):
            current_options = sorted(
                options_by_step.get(int(step.id), []),
                key=lambda value: (int(value.order_index), int(value.id or 0)),
            )
            current_assets = sorted(
                step_assets.get(int(step.id), []),
                key=lambda value: (
                    str(value.asset_type),
                    str(value.usage_context or ""),
                    str(value.manifest_asset_id),
                ),
            )
            rounds.append({
                "order_index": int(step.order_index),
                "prompt_text": str(step.prompt_text or ""),
                "expected_reading_text": (
                    str(step.expected_reading_text)
                    if step.expected_reading_text is not None
                    else None
                ),
                "options": [
                    {
                        "order_index": int(option.order_index),
                        "text": str(option.text),
                        "is_correct": bool(option.is_correct),
                    }
                    for option in current_options
                ],
                "assets": [
                    {
                        "manifest_asset_id": str(asset.manifest_asset_id),
                        "asset_type": str(asset.asset_type),
                        "usage_context": str(asset.usage_context or ""),
                    }
                    for asset in current_assets
                ],
            })

        current_item_assets = sorted(
            item_assets.get(int(item.id), []),
            key=lambda value: (
                str(value.asset_type),
                str(value.usage_context or ""),
                str(value.manifest_asset_id),
            ),
        )
        normalized_items.append({
            "canonical_id": canonical,
            "stable_key": str(item.stable_key),
            "kind": str(item.kind),
            "level_id": int(item.level_id),
            "skill": {
                "skill_key": str(skill.skill_key) if skill is not None else "",
                "canonical_skill_id": str(skill.canonical_skill_id or "") if skill is not None else "",
                "name": str(skill.name) if skill is not None else "",
                "level_id": int(skill.level_id) if skill is not None else None,
            },
            "interaction_type": str(item.interaction_type),
            "order_index": int(item.order_index),
            "version": str(item.version),
            "status": str(item.status),
            "checksum": str(item.checksum),
            "template": _canonical_template(template),
            "item_assets": [
                {
                    "manifest_asset_id": str(asset.manifest_asset_id),
                    "asset_type": str(asset.asset_type),
                    "usage_context": str(asset.usage_context or ""),
                }
                for asset in current_item_assets
            ],
            "rounds": rounds,
        })

    normalized_items.sort(key=lambda value: value["canonical_id"])
    return {"items": normalized_items}


def projection_sha256(db) -> str:
    payload = projection_payload(db)
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
