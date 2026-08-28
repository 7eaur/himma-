"""Canonical Himma content projection for student-facing runtimes.

The approved baseline catalog remains the semantic source of truth for the
original 105 items. Maintenance-approved reinforcement additions are projected
additively so their canonical interactions and approved/reused media behave like
baseline content without rewriting the client source catalog.
"""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from db.models import ContentItem, ContentStep

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO_ROOT / "packages" / "content" / "src" / "catalog.json"
ADDITIONS_PATH = REPO_ROOT / "packages" / "content" / "src" / "reinforcement_additions_v1.json"
VISUAL_PLAN_PATH = REPO_ROOT / "packages" / "content" / "src" / "visual_asset_plan_v1.json"
AUDIO_MANIFEST = REPO_ROOT / "assets" / "audio" / "HIMMA_AUDIO_V1" / "manifest.csv"
IMAGE_MAP = REPO_ROOT / "assets" / "education" / "developer" / "asset-map.json"


def _read_json(path: Path, *, required: bool = True) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        if required:
            raise RuntimeError(f"Approved content metadata is unavailable: {path.name}") from exc
        return {}


def semantic_key(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = re.sub(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]", "", value)
    value = value.replace("ـ", "")
    value = re.sub(r"[^\w\u0600-\u06ff]+", "", value, flags=re.UNICODE)
    if value.startswith("ال"):
        value = value[2:]
    return value.casefold()


def _audio_index() -> dict[str, str]:
    index: dict[str, str] = {}
    try:
        with AUDIO_MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("status") != "approved":
                    continue
                asset_id = str(row.get("id") or "").strip()
                if not asset_id:
                    continue
                for value in (row.get("text_ar"), row.get("spoken_input")):
                    key = semantic_key(str(value or ""))
                    if key:
                        index.setdefault(key, asset_id)
    except OSError:
        pass
    return index


def _image_index() -> dict[str, str]:
    index: dict[str, str] = {}
    payload = _read_json(IMAGE_MAP, required=False)
    for asset in payload.get("assets", []):
        asset_id = str(asset.get("id") or "").strip()
        if not asset_id:
            continue
        for value in (asset.get("label_ar"), asset.get("alt_ar")):
            key = semantic_key(str(value or ""))
            if key:
                index.setdefault(key, asset_id)
    return index


_AUDIO_BY_TEXT = _audio_index()
_IMAGE_BY_TEXT = _image_index()
_VISUAL_PLAN = _read_json(VISUAL_PLAN_PATH, required=False)


def _project_addition(item: dict[str, Any]) -> dict[str, Any]:
    projected = dict(item)
    canonical = str(item.get("canonical_id") or "")
    interaction = str(item.get("interaction") or "")
    explicit_reuse = (_VISUAL_PLAN.get("reuse") or {}).get(canonical, {})
    new_audio_required = {
        semantic_key(str(value))
        for value in (item.get("media") or {}).get("new_audio_required", [])
    }

    rounds: list[dict[str, Any]] = []
    for order_index, source_round in enumerate(item.get("rounds", []), start=1):
        round_data = dict(source_round)
        round_data["order_index"] = order_index
        media: list[dict[str, Any]] = []
        media_gaps: list[dict[str, Any]] = []

        audio_text = str(round_data.get("audio_text") or "").strip()
        if audio_text:
            asset_id = _AUDIO_BY_TEXT.get(semantic_key(audio_text))
            if asset_id:
                media.append({
                    "asset_id": asset_id,
                    "type": "audio",
                    "usage": "prompt",
                    "semantic_text": audio_text,
                })
            elif semantic_key(audio_text) in new_audio_required:
                media_gaps.append({
                    "asset_type": "audio",
                    "usage": "prompt",
                    "semantic_text": audio_text,
                    "status": "missing_approved_asset",
                    "reason": "approved reinforcement explicitly requires this new fixed audio asset",
                })

        sequence = round_data.get("sequence")
        if isinstance(sequence, list):
            for value in sequence:
                semantic_text = str(value)
                asset_id = str(explicit_reuse.get(semantic_text) or "").strip()
                if not asset_id and interaction == "memory_sequence":
                    asset_id = _IMAGE_BY_TEXT.get(semantic_key(semantic_text), "")
                if asset_id:
                    media.append({
                        "asset_id": asset_id,
                        "type": "image",
                        "usage": "illustration",
                        "semantic_text": semantic_text,
                    })

        if media:
            round_data["media"] = media
        if media_gaps:
            round_data["media_gaps"] = media_gaps
        rounds.append(round_data)

    projected["rounds"] = rounds
    return projected


def _load_runtime_catalog() -> dict[str, Any]:
    baseline = _read_json(CATALOG_PATH)
    items = list(baseline.get("items", []))
    additions = _read_json(ADDITIONS_PATH, required=False)
    for item in additions.get("items", []):
        items.append(_project_addition(item))
    return {**baseline, "items": items}


_CATALOG = _load_runtime_catalog()
_ITEMS = {item["canonical_id"]: item for item in _CATALOG.get("items", [])}
_ROUNDS = {
    (item["canonical_id"], int(round_data["order_index"])): round_data
    for item in _CATALOG.get("items", [])
    for round_data in item.get("rounds", [])
    if round_data.get("order_index") is not None
}


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


def _project_approved_media_without_links(item: ContentItem, step: ContentStep) -> list[dict[str, Any]]:
    """Project maintenance-approved additive media without mutating baseline DB rows.

    The 18 reinforcement additions are versioned content already checked into the
    repository. Their reused static media is therefore safe to expose directly
    from the approved manifests even when the additive seed has no historical
    ContentAssetLink rows.
    """
    if not (item.template_data or {}).get("maintenance_addition"):
        return []
    result: list[dict[str, Any]] = []
    image_position = 0
    for media in round_data(item, step).get("media", []):
        asset_id = str(media.get("asset_id") or "").strip()
        asset_type = str(media.get("type") or "").strip()
        if not asset_id or not asset_type:
            continue
        semantic_text = media.get("semantic_text")
        option_id = None
        if asset_type == "image" and media.get("usage") in {"choice", "illustration"}:
            option_id = _option_for_semantic(step, semantic_text, image_position)
            image_position += 1
        result.append({
            "asset_id": asset_id,
            "asset_type": asset_type,
            "usage": media.get("usage"),
            "semantic_text": semantic_text,
            "url": f"/api/media/{asset_id}",
            "option_id": option_id,
        })
    return result


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
    if not result:
        result = _project_approved_media_without_links(item, step)
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
