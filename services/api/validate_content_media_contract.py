"""Validate every media reference in the Sep-8 content contract by stable ID."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from content_approval_contract_2026_09_08 import ITEM_MEDIA, STEP_MEDIA

ROOT = Path(__file__).resolve().parents[2]
IMAGE_MAP = ROOT / "assets" / "education" / "developer" / "asset-map.json"
GENERATED_SEQUENCE_MAP = ROOT / "assets" / "education" / "developer" / "generated-sequence-map.json"
GENERATED_VOCABULARY_MAP = ROOT / "assets" / "education" / "developer" / "generated-vocabulary-map.json"
AUDIO_MANIFEST = ROOT / "assets" / "audio" / "HIMMA_AUDIO_V1" / "manifest.csv"


def _json_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {str(asset.get("id") or "") for asset in payload.get("assets", []) if asset.get("id")}


def image_ids() -> set[str]:
    return _json_ids(IMAGE_MAP) | _json_ids(GENERATED_SEQUENCE_MAP) | _json_ids(GENERATED_VOCABULARY_MAP)


def audio_ids() -> set[str]:
    result: set[str] = set()
    with AUDIO_MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("status") == "approved" and row.get("id"):
                result.add(str(row["id"]).strip())
    return result


def referenced() -> tuple[set[str], set[str]]:
    images: set[str] = set()
    audio: set[str] = set()
    for by_round in STEP_MEDIA.values():
        for specs in by_round.values():
            for asset_id, asset_type, _usage, _semantic in specs:
                (images if asset_type == "image" else audio).add(asset_id)
    for specs in ITEM_MEDIA.values():
        for asset_id, asset_type, _usage, _semantic in specs:
            (images if asset_type == "image" else audio).add(asset_id)
    return images, audio


def validate() -> dict[str, list[str]]:
    wanted_images, wanted_audio = referenced()
    return {
        "missing_images": sorted(wanted_images - image_ids()),
        "missing_audio": sorted(wanted_audio - audio_ids()),
    }


if __name__ == "__main__":
    result = validate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1 if result["missing_images"] or result["missing_audio"] else 0)
