"""Build the single publishable Himma content release.

``canonical_content_compiler`` converts historical/approved content sources into
one structured academic release. This module is the final release boundary: it
resolves every listening prompt against the approved audio manifest by semantic
target, makes the heard target explicit, re-hashes the result, and runs the
fail-closed media inventory guard.

Nothing here writes to the database. The publisher receives only the returned
final object, so there is one canonical release and no post-publication repair
seed or positional media inference.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from canonical_content_compiler import compile_release
from canonical_media_guard import assert_media_contract, resolve_audio_asset

ROOT = Path(__file__).resolve().parents[2]
ADDITION_SOURCES = (
    ROOT / "packages" / "content" / "src" / "reinforcement_additions_v1.json",
    ROOT / "packages" / "content" / "src" / "reinforcement_additions_v2.json",
)


def _rehash(release: dict[str, Any]) -> dict[str, Any]:
    value = deepcopy(release)
    value.pop("sha256", None)
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    value["sha256"] = hashlib.sha256(raw).hexdigest()
    return value


def _addition_audio_targets() -> dict[tuple[str, int], str]:
    """Read explicit ``audio_text`` from approved reinforcement source files."""
    result: dict[tuple[str, int], str] = {}
    for path in ADDITION_SOURCES:
        if not path.is_file():
            raise RuntimeError(f"Missing reinforcement source needed for audio resolution: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        for item in payload.get("items") or []:
            canonical = str(item.get("canonical_id") or "").strip()
            for index, raw in enumerate(item.get("rounds") or [], 1):
                target = str(raw.get("audio_text") or "").strip()
                if not target:
                    continue
                key = (canonical, index)
                if key in result and result[key] != target:
                    raise RuntimeError(f"Conflicting reinforcement audio target for {canonical}/R{index:02d}")
                result[key] = target
    return result


def _existing_prompt_target(step: dict[str, Any]) -> str | None:
    values = {
        str(asset.get("semantic_text") or "").strip()
        for asset in step.get("media") or []
        if str(asset.get("asset_type") or "") == "audio"
        and str(asset.get("usage") or "") == "prompt"
        and str(asset.get("semantic_text") or "").strip()
    }
    if len(values) > 1:
        raise RuntimeError(f"Listening round has conflicting prompt audio semantics: {sorted(values)}")
    return next(iter(values), None)


def _target_for_round(
    canonical: str,
    round_number: int,
    step: dict[str, Any],
    addition_targets: dict[tuple[str, int], str],
) -> str:
    stimulus = step.get("stimulus") or {}
    explicit = str(stimulus.get("audio_target") or "").strip() if isinstance(stimulus, dict) else ""
    source_target = addition_targets.get((canonical, round_number), "")
    existing = _existing_prompt_target(step) or ""

    declared = [value for value in (explicit, source_target, existing) if value]
    if not declared:
        raise RuntimeError(f"{canonical}/R{round_number:02d}: listen interaction has no approved audio target")

    # The latest explicit structured stimulus wins. If no later stimulus exists,
    # the approved reinforcement source wins over historical catalog metadata.
    target = explicit or source_target or existing
    if explicit and source_target and explicit != source_target:
        raise RuntimeError(
            f"{canonical}/R{round_number:02d}: conflicting explicit/source audio targets "
            f"{explicit!r} != {source_target!r}"
        )
    return target


def _resolve_listening_audio(release: dict[str, Any]) -> None:
    """Resolve every listening round by target semantics, never by old asset ID."""
    addition_targets = _addition_audio_targets()
    seen_addition_targets: set[tuple[str, int]] = set()

    for item in release.get("items") or []:
        interaction = str(item.get("interaction_type") or "")
        if not interaction.startswith("listen_"):
            continue
        canonical = str(item.get("canonical_id") or "")
        for step in item.get("rounds") or []:
            round_number = int(step.get("order_index") or 0)
            target = _target_for_round(canonical, round_number, step, addition_targets)
            if (canonical, round_number) in addition_targets:
                seen_addition_targets.add((canonical, round_number))
            asset_id = resolve_audio_asset(target)

            preserved = [
                value for value in step.get("media") or []
                if not (
                    str(value.get("asset_type") or "") == "audio"
                    and str(value.get("usage") or "") == "prompt"
                )
            ]
            preserved.append({
                "asset_id": asset_id,
                "asset_type": "audio",
                "usage": "prompt",
                "semantic_text": target,
            })
            step["media"] = preserved
            step["stimulus"] = {"kind": "audio", "audio_target": target}

    # An approved addition that declares audio_text must actually be a listening
    # round in the final contract; otherwise a later interaction change silently
    # orphaned its required media and must be reviewed explicitly.
    orphaned = sorted(set(addition_targets) - seen_addition_targets)
    if orphaned:
        labels = [f"{canonical}/R{round_number:02d}" for canonical, round_number in orphaned]
        raise RuntimeError(f"Approved reinforcement audio targets are orphaned: {labels}")


def build_canonical_release() -> dict[str, Any]:
    release = deepcopy(compile_release())
    _resolve_listening_audio(release)
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
