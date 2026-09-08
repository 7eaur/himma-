"""Build the single publishable Himma content release.

``canonical_content_compiler`` converts historical/approved content sources into
one structured academic release.  This module is the final release boundary: it
resolves source-supported media corrections, normalizes structured listening
stimuli, re-hashes the resulting object, and runs the fail-closed media guard.

Nothing here writes to the database.  The publisher receives only the returned
final object, so there is still one canonical release and no post-publication
repair seed.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

from canonical_content_compiler import compile_release
from canonical_media_contract_2026_09_08 import ROUND_AUDIO_OVERRIDES
from canonical_media_guard import assert_media_contract


def _rehash(release: dict[str, Any]) -> dict[str, Any]:
    value = deepcopy(release)
    value.pop("sha256", None)
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    value["sha256"] = hashlib.sha256(raw).hexdigest()
    return value


def _item_map(release: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items = {str(item["canonical_id"]): item for item in release.get("items") or []}
    if len(items) != len(release.get("items") or []):
        raise RuntimeError("Duplicate canonical item while resolving media")
    return items


def _apply_audio_overrides(release: dict[str, Any]) -> None:
    items = _item_map(release)
    for (canonical, round_number), desired in ROUND_AUDIO_OVERRIDES.items():
        item = items.get(canonical)
        if item is None:
            raise RuntimeError(f"Canonical media override references missing item {canonical}")
        step = next(
            (value for value in item.get("rounds") or [] if int(value.get("order_index") or 0) == int(round_number)),
            None,
        )
        if step is None:
            raise RuntimeError(f"Canonical media override references missing round {canonical}/R{round_number:02d}")

        current = list(step.get("media") or [])
        non_audio = [value for value in current if str(value.get("asset_type") or "") != "audio"]
        old_audio = [value for value in current if str(value.get("asset_type") or "") == "audio"]
        desired_ids = [str(value["asset_id"]) for value in desired]
        if old_audio and [str(value.get("asset_id") or "") for value in old_audio] not in (
            desired_ids,
            ["LET-01"] if canonical == "L2-CORE-01" and int(round_number) == 2 else [],
        ):
            raise RuntimeError(
                f"{canonical}/R{round_number:02d}: unexpected historical audio contract "
                f"{[value.get('asset_id') for value in old_audio]}"
            )
        step["media"] = non_audio + deepcopy(desired)


def _normalize_listening_stimuli(release: dict[str, Any]) -> None:
    """Make the heard target explicit in structured data for every listen round."""
    for item in release.get("items") or []:
        interaction = str(item.get("interaction_type") or "")
        if not interaction.startswith("listen_"):
            continue
        for step in item.get("rounds") or []:
            prompt_audio = [
                value for value in step.get("media") or []
                if str(value.get("asset_type") or "") == "audio"
                and str(value.get("usage") or "") == "prompt"
            ]
            if len(prompt_audio) != 1:
                raise RuntimeError(
                    f"{item['canonical_id']}/R{int(step.get('order_index') or 0):02d}: "
                    f"listen interaction requires exactly one prompt audio, got {len(prompt_audio)}"
                )
            target = str(prompt_audio[0].get("semantic_text") or "").strip()
            if not target:
                raise RuntimeError(
                    f"{item['canonical_id']}/R{int(step.get('order_index') or 0):02d}: prompt audio has no semantic target"
                )
            step["stimulus"] = {"kind": "audio", "audio_target": target}


def build_canonical_release() -> dict[str, Any]:
    release = deepcopy(compile_release())
    _apply_audio_overrides(release)
    _normalize_listening_stimuli(release)
    release = _rehash(release)
    assert_media_contract(release)
    return release


if __name__ == "__main__":
    current = build_canonical_release()
    print(json.dumps({
        "release_version": current["release_version"],
        "items": len(current["items"]),
        "sha256": current["sha256"],
        "media": "verified",
    }, ensure_ascii=False, indent=2))
