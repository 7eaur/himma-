"""Experimental Arabic pronunciation reference utilities for Himma Speech Lab.

This module parses the *approved, diacritized reference text* into explicit
consonant/vowel/gemination expectations. It does not inspect audio and it does
not produce an academic pronunciation score. Acoustic scoring stays blocked
until a validated model + calibration dataset exist.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
import unicodedata

FATHATAN = "\u064b"
DAMMATAN = "\u064c"
KASRATAN = "\u064d"
FATHA = "\u064e"
DAMMA = "\u064f"
KASRA = "\u0650"
SHADDA = "\u0651"
SUKUN = "\u0652"
DAGGER_ALIF = "\u0670"

_SHORT_VOWELS = {
    FATHA: ("fatha", "فتحة", "a"),
    KASRA: ("kasra", "كسرة", "i"),
    DAMMA: ("damma", "ضمة", "u"),
}
_TANWEEN = {
    FATHATAN: ("fathatan", "تنوين فتح", "an"),
    KASRATAN: ("kasratan", "تنوين كسر", "in"),
    DAMMATAN: ("dammatan", "تنوين ضم", "un"),
}
_MARKS = set(_SHORT_VOWELS) | set(_TANWEEN) | {SHADDA, SUKUN, DAGGER_ALIF}
_ARABIC_LETTER = re.compile(r"[\u0621-\u064a\u0671\u067e\u0686\u06a4\u06af]")


@dataclass(frozen=True)
class PronunciationUnit:
    grapheme: str
    base: str
    vowel: str | None
    vowel_name: str | None
    vowel_symbol: str | None
    geminated: bool
    sukun: bool
    tanween: str | None
    tanween_name: str | None
    phonetic_hint: str


def _is_base_letter(char: str) -> bool:
    return bool(_ARABIC_LETTER.fullmatch(char))


def _clusters(text: str) -> list[str]:
    """Group Arabic base letters with following combining marks."""
    normalized = unicodedata.normalize("NFC", text)
    clusters: list[str] = []
    current = ""
    for char in normalized:
        if _is_base_letter(char):
            if current:
                clusters.append(current)
            current = char
            continue
        if current and (char in _MARKS or unicodedata.combining(char)):
            current += char
            continue
        if current:
            clusters.append(current)
            current = ""
    if current:
        clusters.append(current)
    return clusters


def classify_reference(text: str) -> str:
    """Classify the pedagogical pronunciation target without guessing intent."""
    stripped = text.strip()
    words = [part for part in re.split(r"\s+", stripped) if any(_is_base_letter(c) for c in part)]
    clusters = _clusters(stripped)
    if len(words) >= 8:
        return "passage"
    if len(words) >= 2:
        return "sentence"
    if len(clusters) == 1:
        marks = set(clusters[0][1:])
        if marks & (set(_SHORT_VOWELS) | {SUKUN}):
            return "letter_with_haraka"
        return "single_letter"
    if len(clusters) <= 2 and len(words) <= 1:
        return "syllable"
    return "word"


def pronunciation_units(text: str) -> list[PronunciationUnit]:
    units: list[PronunciationUnit] = []
    for cluster in _clusters(text):
        base = cluster[0]
        marks = set(cluster[1:])
        vowel = None
        vowel_name = None
        vowel_symbol = None
        tanween = None
        tanween_name = None
        hint_parts = [base]

        for symbol, (code, arabic_name, phonetic) in _SHORT_VOWELS.items():
            if symbol in marks:
                vowel = code
                vowel_name = arabic_name
                vowel_symbol = symbol
                hint_parts.append(phonetic)
                break
        for symbol, (code, arabic_name, phonetic) in _TANWEEN.items():
            if symbol in marks:
                tanween = code
                tanween_name = arabic_name
                hint_parts.append(phonetic)
                break

        geminated = SHADDA in marks
        sukun = SUKUN in marks
        if geminated:
            hint_parts.insert(0, f"{base}×2")
        if sukun:
            hint_parts.append("∅")
        if DAGGER_ALIF in marks:
            hint_parts.append("ā")

        units.append(
            PronunciationUnit(
                grapheme=cluster,
                base=base,
                vowel=vowel,
                vowel_name=vowel_name,
                vowel_symbol=vowel_symbol,
                geminated=geminated,
                sukun=sukun,
                tanween=tanween,
                tanween_name=tanween_name,
                phonetic_hint=" + ".join(hint_parts),
            )
        )
    return units


def build_pronunciation_reference(text: str) -> dict:
    """Return a transparent, non-acoustic pronunciation contract for the lab."""
    units = pronunciation_units(text)
    return {
        "target_type": classify_reference(text),
        "reference_text": text,
        "units": [asdict(unit) for unit in units],
        "has_diacritics": any(
            unit.vowel or unit.sukun or unit.geminated or unit.tanween
            for unit in units
        ),
        "acoustic_status": "not_calibrated",
        "academic_effect": "none",
    }
