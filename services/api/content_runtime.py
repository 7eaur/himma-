"""DB-only student-facing content helpers.

All academic/display metadata is imported into PostgreSQL by the content
publisher. Runtime requests never open repository JSON/CSV files, never parse
legacy prompt/source text, and never infer image-option relationships by
position.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

from db.models import ContentItem, ContentStep

DB_RUNTIME_VERSION = "HIMMA-DB-RUNTIME-1.0"
READ = {"read_aloud", "timed_read_aloud"}
LISTEN = {"listen_choose_one", "listen_choose_image", "listen_choose_many"}
ORDER = {"sequence", "memory_sequence", "path_sequence", "build_word"}

ITEM_ASSET_SEMANTIC_FALLBACKS = {
    ("PRE-Q24", "STY-01"): "نص الاختبار القبلي",
}


def semantic_key(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = re.sub(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]", "", value)
    value = value.replace("ـ", "")
    value = re.sub(r"[^\w\u0600-\u06ff]+", "", value, flags=re.UNICODE)
    if value.startswith("ال"):
        value = value[2:]
    return value.casefold()


def active_options(step: ContentStep) -> list:
    """Return only the current option contract in canonical order."""
    return sorted(
        [option for option in step.options if bool(getattr(option, "is_active", True))],
        key=lambda value: (int(value.order_index), int(value.id or 0)),
    )


def canonical_id(item: ContentItem) -> str:
    data = item.template_data or {}
    return str(data.get("canonical_id") or item.stable_key)


def canonical_interaction(item: ContentItem) -> str:
    data = item.template_data or {}
    return str(data.get("canonical_interaction_type") or item.interaction_type)


def _db_runtime(item: ContentItem) -> dict[str, Any]:
    data = item.template_data or {}
    runtime = data.get("db_runtime") or {}
    if runtime and runtime.get("version") != DB_RUNTIME_VERSION:
        return {}
    return runtime


def catalog_item(item: ContentItem) -> dict[str, Any]:
    return dict(_db_runtime(item).get("source_item") or {})


def _runtime_round(item: ContentItem, step: ContentStep) -> dict[str, Any]:
    for value in _db_runtime(item).get("rounds", []):
        if int(value.get("order_index") or 0) == int(step.order_index):
            return value
    return {}


def round_data(item: ContentItem, step: ContentStep) -> dict[str, Any]:
    runtime = _runtime_round(item, step)
    source = dict(runtime.get("source") or {})
    source["media"] = [
        {
            "asset_id": value.get("asset_id"),
            "asset_type": value.get("asset_type"),
            "type": value.get("asset_type"),
            "usage": value.get("usage"),
            "semantic_text": value.get("semantic_text"),
        }
        for value in runtime.get("assets", [])
    ]
    source["media_gaps"] = list(runtime.get("media_gaps") or [])
    return source


def _presentation(item: ContentItem, step: ContentStep) -> dict[str, Any]:
    data = item.template_data or {}
    if item.kind == "pretest_question":
        return dict(data.get("pretest_experience") or {})
    if item.kind == "posttest_question":
        return dict(data.get("posttest_experience") or {})
    if item.kind in {"core_activity", "reinforcement_activity"}:
        experience = data.get("learning_experience") or {}
        for value in experience.get("rounds", []):
            if int(value.get("round_number") or 0) == int(step.order_index):
                return dict(value)
    return {}


def presentation_data(item: ContentItem, step: ContentStep) -> dict[str, Any]:
    return _presentation(item, step)


def _fallback_instruction(interaction: str) -> str:
    if interaction in LISTEN:
        return "استمع جيدًا، ثم اختر الإجابة المناسبة."
    if interaction in READ:
        return "اقرأ النص الظاهر بصوت واضح، ثم أرسل تسجيلك."
    if interaction == "memory_sequence":
        return "تذكّر العناصر جيدًا، ثم أعد ترتيبها كما ظهرت."
    if interaction in ORDER:
        return "اضغط على العناصر بالترتيب الصحيح."
    if interaction in {"choose_image", "choose_many"}:
        return "انظر جيدًا، ثم اختر العناصر المطلوبة."
    return "اقرأ المطلوب، ثم اختر الإجابة المناسبة."


def instruction_text(item: ContentItem, step: ContentStep) -> str:
    value = str(_presentation(item, step).get("instruction_text") or "").strip()
    return value or _fallback_instruction(canonical_interaction(item))


def media_gaps(item: ContentItem, step: ContentStep) -> list[dict[str, Any]]:
    return list(_runtime_round(item, step).get("media_gaps") or [])


def _option_id_by_order(step: ContentStep, order_index: Any) -> int | None:
    try:
        wanted = int(order_index)
    except (TypeError, ValueError):
        return None
    option = next((value for value in active_options(step) if int(value.order_index) == wanted), None)
    return int(option.id) if option is not None else None


def _dedupe_assets(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str, int | None]] = set()
    seen_image_options: set[int] = set()
    for asset in assets:
        option_id = asset.get("option_id")
        normalized_option = int(option_id) if option_id is not None else None
        key = (str(asset.get("asset_id") or ""), str(asset.get("asset_type") or ""), normalized_option)
        if key in seen_keys:
            continue
        if str(asset.get("asset_type") or "") == "image" and normalized_option is not None:
            if normalized_option in seen_image_options:
                continue
            seen_image_options.add(normalized_option)
        seen_keys.add(key)
        result.append(asset)
    return result


def step_assets(item: ContentItem, step: ContentStep) -> list[dict[str, Any]]:
    runtime_assets = list(_runtime_round(item, step).get("assets") or [])
    if runtime_assets:
        result: list[dict[str, Any]] = []
        for value in runtime_assets:
            asset_id = str(value.get("asset_id") or "")
            asset_type = str(value.get("asset_type") or "")
            if not asset_id or not asset_type:
                continue
            usage = value.get("usage")
            option_id = None
            if asset_type == "image" and usage == "choice":
                option_id = _option_id_by_order(step, value.get("option_order_index"))
            result.append({
                "asset_id": asset_id,
                "asset_type": asset_type,
                "usage": usage,
                "semantic_text": value.get("semantic_text"),
                "url": f"/api/media/{asset_id}",
                "option_id": option_id,
            })
        return _dedupe_assets(result)

    # Missing structured runtime data is never permission to guess an
    # option-image relation by list position. Legacy links remain visible only
    # as non-selectable metadata until a semantic mapping is published.
    result: list[dict[str, Any]] = []
    for link in sorted(step.assets, key=lambda value: value.id or 0):
        result.append({
            "asset_id": link.manifest_asset_id,
            "asset_type": link.asset_type,
            "usage": link.usage_context,
            "semantic_text": None,
            "url": f"/api/media/{link.manifest_asset_id}",
            "option_id": None,
        })
    return _dedupe_assets(result)


def item_assets(item: ContentItem) -> list[dict[str, Any]]:
    runtime_assets = list(_db_runtime(item).get("item_assets") or [])
    if runtime_assets:
        return [
            {
                "asset_id": str(value.get("asset_id") or ""),
                "asset_type": str(value.get("asset_type") or ""),
                "usage": value.get("usage"),
                "semantic_text": value.get("semantic_text"),
                "url": f"/api/media/{value.get('asset_id')}",
                "option_id": None,
            }
            for value in runtime_assets
            if value.get("asset_id") and value.get("asset_type")
        ]

    data = item.template_data or {}
    stored_assets = {
        str(value.get("asset_id") or ""): value
        for value in data.get("item_assets", [])
        if value.get("asset_id")
    }
    canonical = canonical_id(item)
    result = []
    for link in sorted(item.assets, key=lambda value: value.id or 0):
        stored = stored_assets.get(link.manifest_asset_id, {})
        semantic = str(
            stored.get("semantic_text")
            or ITEM_ASSET_SEMANTIC_FALLBACKS.get((canonical, link.manifest_asset_id))
            or ""
        ).strip()
        result.append({
            "asset_id": link.manifest_asset_id,
            "asset_type": link.asset_type,
            "usage": link.usage_context,
            "semantic_text": semantic or None,
            "url": f"/api/media/{link.manifest_asset_id}",
            "option_id": None,
        })
    return result
