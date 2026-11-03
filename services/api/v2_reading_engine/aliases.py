"""Native V2 letter alias contract; no dependency on the speech laboratory.

This module is pure: it never calls Azure, writes grades or accepts a recording
without the caller's explicit quality and recognition checks.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import json
import unicodedata


_CATALOG_FILE = Path(__file__).resolve().parent / "data" / "approved_letter_aliases_v1_2.json"
_EDGE_PUNCTUATION = " \t\n\r\f\v.,!?:;؛،؟。！？，、\"'“”‘’()[]{}ـ"
_DIACRITICS = set(chr(c) for c in range(0x064B, 0x0653)) | {"\u0670"}


@dataclass(frozen=True)
class LetterMatch:
    matched: bool
    reference: str
    matched_alias: str | None = None
    candidate_kind: str | None = None
    catalog_version: str | None = None

    @property
    def vowel_verified(self) -> bool:
        # Transcript spelling is not acoustic evidence for a short vowel.
        return False


def _normalize(value: str) -> str:
    return (unicodedata.normalize("NFKC", value)
            .strip(_EDGE_PUNCTUATION)
            .lower()
            .translate(str.maketrans({"إ": "ا", "أ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي"})))


@lru_cache(maxsize=1)
def load_alias_catalog() -> dict:
    """Validate the immutable owner-approved data before use."""
    payload = json.loads(_CATALOG_FILE.read_text(encoding="utf-8"))
    if payload.get("schemaVersion") != "himma-v2-owner-approved-letter-aliases/1.2":
        raise ValueError("Unexpected V2 letter alias policy version")
    if payload.get("rules", {}).get("onValidApprovedAliasMatch") != "correct_100_percent":
        raise ValueError("Letter alias policy is not owner-approved")
    cases = payload.get("cases")
    if not isinstance(cases, dict) or len(cases) != 10:
        raise ValueError("Expected exactly 10 letter question identities")
    total = 0
    for question_id, entry in cases.items():
        if not isinstance(question_id, str) or not question_id:
            raise ValueError("Invalid question ID")
        reference = entry.get("reference")
        variants = entry.get("variants")
        if not isinstance(reference, str) or not reference or not isinstance(variants, list):
            raise ValueError("Invalid letter alias entry")
        used = {_normalize(reference)}
        for variant in variants:
            if not isinstance(variant, dict) or not isinstance(variant.get("text"), str):
                raise ValueError("Invalid letter alias spelling")
            norm = _normalize(variant["text"])
            if not norm or norm in used:
                raise ValueError("Duplicated or empty alias")
            used.add(norm)
            total += 1
    if total != 31:
        raise ValueError("Expected exactly 31 owner-approved letter alternatives")
    return payload


def match_letter_transcript(*, question_id: str, reference: str,
                            transcript: str | None) -> LetterMatch:
    """Match only this exact question and its original vowelled reference.

    Other questions' aliases, approximate matches and wrong explicit Arabic
    harakat are never silently accepted.
    """
    catalog = load_alias_catalog()
    entry = catalog["cases"].get(question_id)
    if entry is None or entry["reference"] != reference:
        return LetterMatch(False, reference)
    if not isinstance(transcript, str) or not transcript.strip():
        return LetterMatch(False, reference)

    observed = _normalize(transcript)
    expected = _normalize(reference)
    if not observed:
        return LetterMatch(False, reference)
    if observed == expected:
        return LetterMatch(True, reference, reference, "exact_reference",
                           catalog["schemaVersion"])
    if any(char in _DIACRITICS for char in observed):
        return LetterMatch(False, reference)

    for item in entry["variants"]:
        if _normalize(item["text"]) == observed:
            return LetterMatch(True, reference, item["text"], item["kind"],
                               catalog["schemaVersion"])
    return LetterMatch(False, reference)
