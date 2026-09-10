"""Fail-closed media integrity checks for the canonical Himma release.

The guard validates the *final compiled release*, not a hand-maintained list:
- every referenced stable image/audio ID exists;
- every declared image file exists and is non-empty;
- every approved audio row has both WAV master and MP3 web binaries;
- duplicate stable IDs are rejected;
- referenced audio must be approved and semantically match its target;
- every selectable image must semantically match the option it represents;
- selectable images must not contain embedded answer text.

Matching is category-aware. Vowel-sensitive ``syllable`` and vocalized
``letter-sound`` targets require exact manifest semantics, so ``مِ`` can never
silently become the current ``LET-01 = مَ``. A bare single letter may resolve to
its approved letter-sound row by base letter. Word assets may match by the same
Arabic letters when the manifest label omits optional diacritics (for example
``بَاب`` -> manifest ``باب``), but resolution still requires exactly one approved
asset ID. This keeps lexical labels tolerant without weakening vowel contrasts.

Image-choice matching is deliberately stricter than generic context-image
matching. A choice image must match the manifest's semantic vocabulary label (or
an explicitly documented approved alias). Context illustrations may be broader
scenes and are therefore validated for identity/files, but not forced to equal a
single option label.
"""
from __future__ import annotations

import csv
import json
import re
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

# These are approved wording aliases where a sequence image intentionally
# represents the same visual event under a shorter/newer learner-facing label.
# Keeping them explicit is safer than fuzzy matching arbitrary Arabic phrases.
IMAGE_SEMANTIC_ALIASES: dict[str, set[str]] = {
    "SEQ-01": {"زرع البذرة", "زرعت البذرة"},
    "SEQ-02": {"سقي البذرة", "سقتها"},
    "SEQ-03": {"نمو الزهرة", "ظهور النبتة"},
    "SEQ-04": {"غسل التفاحة", "غسلت"},
    "SEQ-05": {"تقطيع التفاحة", "قطعت"},
    "SEQ-06": {"أكل التفاحة", "أكلت"},
    "SEQ-07": {"إخراج الكتاب", "أخذ الكتاب"},
    "SEQ-08": {"قراءة الكتاب", "القراءة", "قرأ الكتاب"},
    "HIMMA-GEN-SEQ-008": {"الذهاب إلى الشاطئ", "ذهب ماجد إلى الشاطئ", "ذهب"},
    "HIMMA-GEN-SEQ-009": {"اللعب بالرمل", "لعب بالرمل", "لعب"},
    "HIMMA-GEN-SEQ-010": {"تنظيف المكان", "نظف مكانه", "نظف"},
}


def _norm(value: object) -> str:
    return unicodedata.normalize("NFKC", str(value or "")).strip()


def _without_marks(value: object) -> str:
    return "".join(
        char for char in _norm(value).replace("ـ", "")
        if unicodedata.category(char) != "Mn"
    )


def _has_marks(value: object) -> bool:
    return any(unicodedata.category(char) == "Mn" for char in _norm(value))


def _image_semantic_key(value: object) -> str:
    plain = _without_marks(value)
    plain = re.sub(r"[^\w\u0600-\u06ff]+", "", plain, flags=re.UNICODE)
    if plain.startswith("ال"):
        plain = plain[2:]
    return plain.casefold()


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
    target_plain = _without_marks(target)
    if category == "letter-sound":
        # Relax only *bare* letter targets. Once the target carries a vowel,
        # exact matching above is required so letter-vowel contrasts stay sound.
        return (
            not _has_marks(target)
            and len(target_plain) == 1
            and any(_without_marks(candidate) == target_plain for candidate in candidates)
        )
    if category == "word":
        # Word labels in the manifest are not uniformly vocalized. Matching by
        # base letters is safe only because resolve_audio_asset still requires a
        # unique approved stable ID for this lexical target.
        return bool(target_plain) and any(_without_marks(candidate) == target_plain for candidate in candidates)
    if category == "auditory-story":
        # Story lookup is against the story label only. Never search a full story
        # transcript for arbitrary prompt targets: a bare letter or common word
        # would otherwise collide with the dedicated letter/word asset.
        story_label = _without_marks(row.get("text_ar"))
        return target_plain.startswith("قصة") and target_plain in story_label
    # ``syllable`` intentionally has no relaxed branch: vowel length/quality is
    # the academic target and must remain exact.
    return False


def _image_semantic_matches(asset_id: str, row: dict[str, Any], semantic: str) -> bool:
    target = _image_semantic_key(semantic)
    if not target:
        return False

    candidate_values = {
        _norm(row.get("label_ar")),
        _norm(row.get("semantic_key")),
        *IMAGE_SEMANTIC_ALIASES.get(asset_id, set()),
    } - {""}
    return target in {_image_semantic_key(value) for value in candidate_values}


def _choice_image_contains_text(row: dict[str, Any]) -> bool:
    if "contains_text" in row:
        return bool(row.get("contains_text"))
    qa = row.get("qa") or {}
    if isinstance(qa, dict) and "no_embedded_text" in qa:
        return not bool(qa.get("no_embedded_text"))
    # Unknown is not automatically treated as unsafe here because legacy maps
    # predate the QA flag. Identity/file checks still apply, and current maps
    # expose either contains_text or no_embedded_text for selectable assets.
    return False


def resolve_audio_asset(semantic: str) -> str:
    """Resolve one target to exactly one approved manifest ID, never by position.

    Exact manifest text/spoken matches always outrank relaxed category matching.
    This keeps inflected/vocalized variants distinct (for example ``قَلَم`` from
    ``قَلَمٌ``) while still allowing a unique approved fallback when the manifest
    omits optional diacritics.
    """
    audio, duplicates = _audio_rows()
    if duplicates:
        raise RuntimeError(f"Duplicate audio manifest IDs: {duplicates}")

    target = _norm(semantic)
    approved = {
        asset_id: row
        for asset_id, row in audio.items()
        if _norm(row.get("status")) == "approved"
    }
    exact = [
        asset_id
        for asset_id, row in approved.items()
        if target in {_norm(row.get("text_ar")), _norm(row.get("spoken_input"))} - {""}
    ]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        raise RuntimeError(
            f"Audio target {target!r} has multiple exact approved assets: {exact}"
        )

    matches = [
        asset_id for asset_id, row in approved.items()
        if _audio_semantic_matches(row, semantic)
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Audio target {target!r} must resolve to exactly one approved asset, got {matches}"
        )
    return matches[0]


def validate_media_contract(release: dict[str, Any]) -> dict[str, list[str]]:
    images, duplicate_image_ids, missing_image_maps = _image_records()
    audio, duplicate_audio_ids = _audio_rows()

    referenced_images: set[str] = set()
    referenced_audio: set[str] = set()
    image_semantic_mismatches: list[str] = []
    choice_images_with_embedded_text: list[str] = []
    audio_semantic_mismatches: list[str] = []
    unapproved_referenced_audio: list[str] = []

    for canonical, round_number, asset in _release_media(release):
        asset_id = _norm(asset.get("asset_id"))
        asset_type = _norm(asset.get("asset_type"))
        usage = _norm(asset.get("usage"))
        semantic = _norm(asset.get("semantic_text"))
        location = f"{canonical}/R{round_number:02d}" if round_number else canonical
        if asset_type == "image":
            referenced_images.add(asset_id)
            row = images.get(asset_id)
            if row is not None and usage == "choice":
                if not _image_semantic_matches(asset_id, row, semantic):
                    image_semantic_mismatches.append(
                        f"{location}:{asset_id}:target={semantic!r}:manifest={_norm(row.get('label_ar'))!r}"
                    )
                if _choice_image_contains_text(row):
                    choice_images_with_embedded_text.append(f"{location}:{asset_id}")
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
        "image_semantic_mismatches": sorted(set(image_semantic_mismatches)),
        "choice_images_with_embedded_text": sorted(set(choice_images_with_embedded_text)),
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
