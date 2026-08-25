"""Canonical Himma content projection for student-facing runtimes.

The approved catalog is the semantic source of truth. Database rows remain
stable for accepted historical stages, while this module restores the richer
interaction type and the approved media metadata needed by the current UI.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from db.models import ContentItem, ContentStep

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO_ROOT / "packages" / "content" / "src" / "catalog.json"


def _load_catalog() -> dict[str, Any]:
    try:
        return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("Approved content catalog is unavailable") from exc


_CATALOG = _load_catalog()
_ITEMS = {item["canonical_id"]: item for item in _CATALOG.get("items", [])}
_ROUNDS = {
    (item["canonical_id"], int(round_data["order_index"])): round_data
    for item in _CATALOG.get("items", [])
    for round_data in item.get("rounds", [])
}


def semantic_key(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = re.sub(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]", "", value)
    value = value.replace("ـ", "")
    value = re.sub(r"[^\w\u0600-\u06ff]+", "", value, flags=re.UNICODE)
    if value.startswith("ال"):
        value = value[2:]
    return value.casefold()


def canonical_id(item: ContentItem) -> str:
    data = item.template_data or {}
    return str(data.get("canonical_id") or item.stable_key)


def canonical_interaction(item: ContentItem) -> str:
    data = item.template_data or {}
    return str(data.get("canonical_interaction_type") or item.interaction_type)


def catalog_item(item: ContentItem) -> dict[str, Any]:
    return _ITEMS.get(canonical_id(item), {})


def round_data(item: ContentItem, step: ContentStep) -> dict[str, Any]:
    return _ROUNDS.get((canonical_id(item), int(step.order_index)), {})


def _instruction(interaction: str, *, expected_reading_text: str | None = None) -> str:
    if interaction == "choose_one":
        return "اختر الإجابة الصحيحة."
    if interaction == "listen_choose_one":
        return "استمع جيدًا، ثم اختر الإجابة الصحيحة."
    if interaction == "choose_image":
        return "اختر الصورة الصحيحة."
    if interaction == "listen_choose_image":
        return "استمع جيدًا، ثم اختر الصورة الصحيحة."
    if interaction == "choose_many":
        return "اختر كل الإجابات الصحيحة."
    if interaction == "listen_choose_many":
        return "استمع جيدًا، ثم اختر الصور الصحيحة."
    if interaction == "sequence":
        return "رتّب العناصر بالترتيب الصحيح."
    if interaction == "memory_sequence":
        return "تذكّر الصور، ثم رتّبها كما ظهرت."
    if interaction == "path_sequence":
        return "اتبع المسار بالترتيب من اليمين إلى اليسار."
    if interaction == "build_word":
        return "كوّن الكلمة بترتيب الحروف الصحيح."
    if interaction == "timed_read_aloud":
        return "اقرأ النص بصوت واضح عند بدء التسجيل."
    if interaction == "read_aloud":
        return "اقرأ النص الظاهر بصوت واضح."
    return "أكمل المهمة التالية."


def instruction_text(item: ContentItem, step: ContentStep) -> str:
    return _instruction(
        canonical_interaction(item),
        expected_reading_text=step.expected_reading_text,
    )


def media_gaps(item: ContentItem, step: ContentStep) -> list[dict[str, Any]]:
    return list(round_data(item, step).get("media_gaps", []))


def _option_for_semantic(step: ContentStep, semantic_text: str | None, position: int) -> int | None:
    if not step.options:
        return None
    semantic = semantic_key(semantic_text or "")
    if semantic:
        exact = [option for option in step.options if semantic_key(option.text) == semantic]
        if exact:
            return exact[0].id
        contained = [
            option
            for option in step.options
            if semantic in semantic_key(option.text) or semantic_key(option.text) in semantic
        ]
        if contained:
            return contained[0].id
    if position < len(step.options):
        return step.options[position].id
    return None


def step_assets(item: ContentItem, step: ContentStep) -> list[dict[str, Any]]:
    approved = round_data(item, step).get("media", [])
    by_id: dict[str, list[dict[str, Any]]] = {}
    for media in approved:
        by_id.setdefault(str(media.get("asset_id")), []).append(media)

    result: list[dict[str, Any]] = []
    image_position = 0
    for link in step.assets:
        candidates = by_id.get(link.manifest_asset_id, [])
        semantic = candidates.pop(0) if candidates else {}
        option_id = None
        if link.asset_type == "image" and link.usage_context in {"choice", "illustration"}:
            option_id = _option_for_semantic(step, semantic.get("semantic_text"), image_position)
            image_position += 1
        result.append(
            {
                "asset_id": link.manifest_asset_id,
                "asset_type": link.asset_type,
                "usage": link.usage_context,
                "semantic_text": semantic.get("semantic_text"),
                "url": f"/api/media/{link.manifest_asset_id}",
                "option_id": option_id,
            }
        )
    return result


def item_assets(item: ContentItem) -> list[dict[str, Any]]:
    approved = catalog_item(item).get("item_assets", [])
    by_id = {str(media.get("asset_id")): media for media in approved}
    return [
        {
            "asset_id": link.manifest_asset_id,
            "asset_type": link.asset_type,
            "usage": link.usage_context,
            "semantic_text": by_id.get(link.manifest_asset_id, {}).get("semantic_text"),
            "url": f"/api/media/{link.manifest_asset_id}",
            "option_id": None,
        }
        for link in item.assets
    ]
