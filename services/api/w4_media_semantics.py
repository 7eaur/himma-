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

from typing import Any


LEXICAL_STIMULUS_CONTRACT: dict[tuple[str, int], dict[str, str]] = {
    ("L2-CORE-09", 3): {
        "asset_id": "VOC-05",
        "semantic_text": "سَمَك",
    },
    ("L2-CORE-09", 5): {
        "asset_id": "VOC-15",
        "semantic_text": "نُور",
    },
}


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
