"""Non-academic acoustic evidence planning for Arabic pronunciation.

This module intentionally does not score recordings. It turns the approved,
diacritized reference into an explicit collection/calibration contract so that
future acoustic models can be evaluated without confusing ASR confidence with
haraka or consonant correctness.
"""

from __future__ import annotations

from arabic_pronunciation import build_pronunciation_reference

_STT_LOCALE = "ar-OM"
_AZURE_PRONUNCIATION_CANDIDATES = ("ar-SA", "ar-EG")

_VOWEL_CONTRASTS = {
    "fatha": ("kasra", "damma", "sukun"),
    "kasra": ("fatha", "damma", "sukun"),
    "damma": ("fatha", "kasra", "sukun"),
    "sukun": ("fatha", "kasra", "damma"),
}


def _expected_class(unit: dict) -> str | None:
    if unit.get("sukun"):
        return "sukun"
    if unit.get("vowel"):
        return str(unit["vowel"])
    return None


def build_acoustic_evidence_plan(reference_text: str) -> dict:
    """Build a transparent plan for collecting/calibrating acoustic evidence.

    No value in this response is a pronunciation judgement. In particular,
    provider confidence and lexical ASR output must never be copied into the
    acoustic score fields produced by this contract.
    """
    pronunciation = build_pronunciation_reference(reference_text)
    units: list[dict] = []

    for index, unit in enumerate(pronunciation["units"]):
        expected = _expected_class(unit)
        units.append(
            {
                "unit_index": index,
                "grapheme": unit["grapheme"],
                "base": unit["base"],
                "expected_vowel_class": expected,
                "contrast_vowel_classes": list(_VOWEL_CONTRASTS.get(expected, ())),
                "expects_gemination": bool(unit["geminated"]),
                "expects_tanween": unit["tanween"],
                "acoustic_score": None,
                "acoustic_label": None,
                "evidence_status": "pending_calibration",
            }
        )

    return {
        "status": "collection_required",
        "reference_text": reference_text,
        "target_type": pronunciation["target_type"],
        "stt_locale": _STT_LOCALE,
        "azure_pronunciation_assessment": {
            "enabled_for_judgement": False,
            "candidate_locales": list(_AZURE_PRONUNCIATION_CANDIDATES),
            "note": "benchmark_only_not_direct_haraka_judgement",
        },
        "direct_haraka_judgement": False,
        "requires_ground_truth": True,
        "calibration_version": None,
        "units": units,
        "academic_effect": "none",
    }
