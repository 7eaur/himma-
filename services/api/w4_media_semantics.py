"""Owner-approved W4 lexical-media semantics.

This module applies only the narrow 2026-09-14 owner/client decision for
AUD-MEDIA-002. Historical source catalogs remain immutable migration inputs;
the newer semantic authority is folded into the final canonical release before
it is hashed and published.

The two approved direct lexical stimuli are:
- L2-CORE-09/R03: سَمَك -> VOC-05 (fish)
- L2-CORE-09/R05: نُور -> VOC-15 (light/lamp)

No other media row is changed here.
"""
from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
IMAGE_MAP = ROOT / "assets" / "education" / "developer" / "asset-map.json"

LEXICAL_STIMULUS_CONTRACT: dict[tuple[str, int], dict[str, str]] = {
    ("L2-CORE-09", 3): {
        "asset_id": "VOC-05",
        "semantic_text": "سَمَك",
        "manifest_label_ar": "سمكة",
    },
    ("L2-CORE-09", 5): {
        "asset_id": "VOC-15",
        "semantic_text": "نُور",
        "manifest_label_ar": "مصباح أو ضوء",
    },
}


def _plain(value: object) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or "")).replace("ـ", "")
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn").strip()


def _manifest_labels() -> dict[str, str]:
    if not IMAGE_MAP.is_file():
        raise RuntimeError(f"Missing canonical image map: {IMAGE_MAP}")
    payload = json.loads(IMAGE_MAP.read_text(encoding="utf-8"))
    return {
        str(asset.get("id") or "").strip(): str(asset.get("label_ar") or "").strip()
        for asset in payload.get("assets") or []
        if str(asset.get("id") or "").strip()
    }


def validate_w4_lexical_media_semantics(release: dict[str, Any]) -> list[str]:
    """Return exact W4 lexical-contract mismatches without mutating the release."""
    by_id = {
        str(item.get("canonical_id") or ""): item
        for item in release.get("items") or []
    }
    labels = _manifest_labels()
    failures: list[str] = []

    for (canonical, round_number), expected in LEXICAL_STIMULUS_CONTRACT.items():
        item = by_id.get(canonical)
        if item is None:
            failures.append(f"{canonical}:missing-item")
            continue
        rounds = {
            int(step.get("order_index") or 0): step
            for step in item.get("rounds") or []
        }
        step = rounds.get(round_number)
        location = f"{canonical}/R{round_number:02d}"
        if step is None:
            failures.append(f"{location}:missing-round")
            continue

        image_media = [
            asset
            for asset in step.get("media") or []
            if str(asset.get("asset_type") or "") == "image"
        ]
        if len(image_media) != 1:
            failures.append(f"{location}:image-count={len(image_media)}")
            continue
        asset = image_media[0]
        asset_id = str(asset.get("asset_id") or "").strip()
        usage = str(asset.get("usage") or "").strip()
        semantic = str(asset.get("semantic_text") or "").strip()

        if asset_id != expected["asset_id"]:
            failures.append(f"{location}:asset={asset_id}:expected={expected['asset_id']}")
        if usage != "lexical_stimulus":
            failures.append(f"{location}:usage={usage}:expected=lexical_stimulus")
        if _plain(semantic) != _plain(expected["semantic_text"]):
            failures.append(
                f"{location}:semantic={semantic!r}:expected={expected['semantic_text']!r}"
            )
        manifest_label = labels.get(expected["asset_id"], "")
        if manifest_label != expected["manifest_label_ar"]:
            failures.append(
                f"{location}:manifest-label={manifest_label!r}:"
                f"expected={expected['manifest_label_ar']!r}"
            )
    return failures


def assert_w4_lexical_media_semantics(release: dict[str, Any]) -> None:
    failures = validate_w4_lexical_media_semantics(release)
    if failures:
        raise RuntimeError("W4 lexical media contract failed: " + "; ".join(failures))


def apply_w4_lexical_media_semantics(release: dict[str, Any]) -> None:
    """Promote approved direct lexical images out of generic context semantics.

    Fail closed if the compiled source no longer contains exactly the approved
    image identity. This prevents a later positional swap from being silently
    re-labelled as an approved lexical stimulus.
    """
    by_id = {
        str(item.get("canonical_id") or ""): item
        for item in release.get("items") or []
    }

    for (canonical, round_number), expected in LEXICAL_STIMULUS_CONTRACT.items():
        item = by_id.get(canonical)
        if item is None:
            raise RuntimeError(f"W4 lexical contract references missing item {canonical}")

        rounds = {
            int(step.get("order_index") or 0): step
            for step in item.get("rounds") or []
        }
        step = rounds.get(round_number)
        if step is None:
            raise RuntimeError(
                f"W4 lexical contract references missing round {canonical}/R{round_number:02d}"
            )

        image_media = [
            asset
            for asset in step.get("media") or []
            if str(asset.get("asset_type") or "") == "image"
        ]
        matching = [
            asset
            for asset in image_media
            if str(asset.get("asset_id") or "") == expected["asset_id"]
        ]
        if len(image_media) != 1 or len(matching) != 1:
            actual = [str(asset.get("asset_id") or "") for asset in image_media]
            raise RuntimeError(
                f"{canonical}/R{round_number:02d}: approved lexical image "
                f"{expected['asset_id']} is not the unique compiled image; actual={actual}"
            )

        asset = matching[0]
        asset["usage"] = "lexical_stimulus"
        asset["semantic_text"] = expected["semantic_text"]
        asset.pop("option_order_index", None)

    assert_w4_lexical_media_semantics(release)
