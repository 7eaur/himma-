"""Fail-closed media integrity checks for the canonical Himma release.

The guard validates the *final compiled release*, not a hand-maintained list:
- every referenced stable image/audio ID exists;
- every declared image file exists and is non-empty;
- every approved audio row has both WAV master and MP3 web binaries;
- duplicate stable IDs are rejected;
- referenced audio must be approved and semantically match its target.

A bare letter target may use the approved letter-sound recording with a vowel or
sukoon (for example ``م`` -> ``مَ`` or ``ب`` -> ``بْ``). A vocalized target such
as ``مِ`` must match exactly and cannot silently reuse another vowel.
"""
from __future__ import annotations

import csv
import json
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EDUCATION_ROOT = ROOT / "assets" / "education"
IMAGE_MAPS = (
    EDUCATION_ROOT / "developer" / "asset-map.json",
    EDUCATION_ROOT / "developer" / "generated-sequence-map.json",
    EDUCATION_ROOT / "developer" / "generated-vocabulary-map.json",
)
AUDIO_ROOT = ROOT / "assets" / "audio" / "HIMMA_AUDIO_V1"
AUDIO_MANIFEST = AUDIO_ROOT / "manifest.csv"


def _norm(value: object) -> str:
    return unicodedata.normalize("NFKC", str(value or "")).strip()


def _without_marks(value: object) -> str:
    return "".join(
        char for char in _norm(value).replace("ـ", "")
        if unicodedata.category(char) != "Mn"
    )


def _has_marks(value: object) -> bool:
    return any(unicodedata.category(char) == "Mn" for char in _norm(value))


def _image_records() -> tuple[dict[str, dict[str, Any]], list[str], list[str]]:
    rows: list[tuple[str, dict[str, Any]]] = []
    missing_maps: list[str] = []
    for path in IMAGE_MAPS:
        if not path.is_file():
            missing_maps.append(str(path.relative_to(ROOT)))
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for raw in payload.get("assets") or []:
            asset_id = _norm(raw.get("id"))
            if asset_id:
                rows.append((asset_id, dict(raw)))
    counts = Counter(asset_id for asset_id, _ in rows)
    duplicates = sorted(asset_id for asset_id, count in counts.items() if count > 1)
    records = {asset_id: raw for asset_id, raw in rows}
    return records, duplicates, missing_maps


def _audio_rows() -> tuple[dict[str, dict[str, str]], list[str]]:
    if not AUDIO_MANIFEST.is_file():
        return {}, []
    rows: list[tuple[str, dict[str, str]]] = []
    with AUDIO_MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
        for raw in csv.DictReader(handle):
            asset_id = _norm(raw.get("id"))
            if asset_id:
                rows.append((asset_id, {str(k): str(v or "").strip() for k, v in raw.items()}))
    counts = Counter(asset_id for asset_id, _ in rows)
    duplicates = sorted(asset_id for asset_id, count in counts.items() if count > 1)
    return {asset_id: raw for asset_id, raw in rows}, duplicates


def _release_media(release: dict[str, Any]):
    for item in release.get("items") or []:
        canonical = str(item.get("canonical_id") or "")
        for asset in item.get("item_assets") or []:
            yield canonical, 0, dict(asset)
        for step in item.get("rounds") or []:
            round_number = int(step.get("order_index") or 0)
            for asset in step.get("media") or []:
                yield canonical, round_number, dict(asset)


def _audio_semantic_matches(row: dict[str, str], semantic: str) -> bool:
    target = _norm(semantic)
    if not target:
        return False
    candidates = {_norm(row.get("text_ar")), _norm(row.get("spoken_input"))} - {""}
    if target in candidates:
        return True

    category = _norm(row.get("category"))
    if category == "letter-sound" and not _has_marks(target) and len(_without_marks(target)) == 1:
        return any(_without_marks(candidate) == _without_marks(target) for candidate in candidates)
    if category == "auditory-story":
        target_plain = _without_marks(target)
        return any(target_plain and target_plain in _without_marks(candidate) for candidate in candidates)
    return False


def validate_media_contract(release: dict[str, Any]) -> dict[str, list[str]]:
    images, duplicate_image_ids, missing_image_maps = _image_records()
    audio, duplicate_audio_ids = _audio_rows()

    referenced_images: set[str] = set()
    referenced_audio: set[str] = set()
    audio_semantic_mismatches: list[str] = []
    unapproved_referenced_audio: list[str] = []

    for canonical, round_number, asset in _release_media(release):
        asset_id = _norm(asset.get("asset_id"))
        asset_type = _norm(asset.get("asset_type"))
        semantic = _norm(asset.get("semantic_text"))
        location = f"{canonical}/R{round_number:02d}" if round_number else canonical
        if asset_type == "image":
            referenced_images.add(asset_id)
        elif asset_type == "audio":
            referenced_audio.add(asset_id)
            row = audio.get(asset_id)
            if row is not None:
                if _norm(row.get("status")) != "approved":
                    unapproved_referenced_audio.append(f"{location}:{asset_id}")
                if not _audio_semantic_matches(row, semantic):
                    audio_semantic_mismatches.append(
                        f"{location}:{asset_id}:target={semantic!r}:manifest={_norm(row.get('text_ar'))!r}"
                    )

    missing_image_files: list[str] = []
    empty_image_files: list[str] = []
    for asset_id, row in sorted(images.items()):
        files = row.get("files") or {}
        if not isinstance(files, dict) or not files:
            missing_image_files.append(f"{asset_id}:<no-files-declared>")
            continue
        for variant, relative in sorted(files.items()):
            path = EDUCATION_ROOT / str(relative)
            label = f"{asset_id}:{variant}:{relative}"
            if not path.is_file():
                missing_image_files.append(label)
            elif path.stat().st_size <= 0:
                empty_image_files.append(label)

    missing_audio_files: list[str] = []
    empty_audio_files: list[str] = []
    for asset_id, row in sorted(audio.items()):
        if _norm(row.get("status")) != "approved":
            continue
        for field, folder in (("filename_wav", "wav_master"), ("filename_mp3", "web_mp3")):
            filename = _norm(row.get(field))
            label = f"{asset_id}:{field}:{filename or '<missing-name>'}"
            if not filename:
                missing_audio_files.append(label)
                continue
            path = AUDIO_ROOT / folder / filename
            if not path.is_file():
                missing_audio_files.append(label)
            elif path.stat().st_size <= 0:
                empty_audio_files.append(label)

    return {
        "missing_image_maps": sorted(missing_image_maps),
        "duplicate_image_ids": duplicate_image_ids,
        "duplicate_audio_ids": duplicate_audio_ids,
        "missing_referenced_images": sorted(referenced_images - set(images)),
        "missing_referenced_audio": sorted(referenced_audio - set(audio)),
        "unapproved_referenced_audio": sorted(set(unapproved_referenced_audio)),
        "audio_semantic_mismatches": sorted(set(audio_semantic_mismatches)),
        "missing_image_files": missing_image_files,
        "empty_image_files": empty_image_files,
        "missing_audio_files": missing_audio_files,
        "empty_audio_files": empty_audio_files,
    }


def assert_media_contract(release: dict[str, Any]) -> dict[str, list[str]]:
    result = validate_media_contract(release)
    failures = {key: values for key, values in result.items() if values}
    if failures:
        raise RuntimeError(
            "Canonical media contract failed: "
            + json.dumps(failures, ensure_ascii=False, sort_keys=True)
        )
    return result
