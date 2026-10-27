"""Reviewed mapping between diagnostic authoring terms and support focus."""

from __future__ import annotations

from typing import Any


EXPLICIT_HOLD_QUESTION_IDS: set[str] = set()

FOCUS_ALIASES: dict[str, str] = {
    "syllable_decoding": "syllable_reading",
    "blending_breakdown": "syllable_blending",
    "blending_order": "syllable_blending",
    "semantic_guess": "word_decoding",
    "missing_letter": "spelling",
    "chunking_error": "chunking",
    "omission": "blending",
    "hesitation": "pause_or_order",
    "word_order": "word_order",
    "broken_link": "pause_or_order",
    "natural_pacing": "pause_or_order",
    "word_substitution": "word_omission",
    "unsupported_guess": "find_explicit_answer",
    "who_confusion": "find_explicit_answer",
    "when_confusion": "find_explicit_answer",
    "time_confusion": "find_explicit_answer",
    "order_confusion": "event_sequence",
    "semantic_incoherence": "sentence_writing",
    "incomplete_sentence": "sentence_writing",
}


def resolve_question_focus(question: dict[str, Any], support: dict[str, Any]) -> str | None:
    available = set(support.get("focus") or [])
    error_focus = str(question.get("error_focus") or "")
    evidence_type = str(question.get("evidence_type") or "")

    if error_focus in available:
        focus = error_focus
    elif error_focus == "word_order" and "pause_or_order" in available:
        focus = "pause_or_order"
    elif error_focus == "vowel_confusion":
        focus = next((name for name in ("fatha", "damma", "kasra") if name in evidence_type), "")
        if not focus and evidence_type == "short_vowel_mixed":
            # The test measures recognition of the TARGET vowel, not a guessed
            # misconception from a wrong option. Infer it from the private
            # correct answer in the learner's pinned immutable question.
            correct_ids = set((question.get("private_answer") or {}).get("correct_option_ids") or [])
            matching = [option for option in question.get("options", [])
                        if option.get("id") in correct_ids]
            if len(matching) == 1:
                text = str(matching[0].get("text") or "")
                vowels = {"َ": "fatha", "ُ": "damma", "ِ": "kasra"}
                matches = {vowels[character] for character in text if character in vowels}
                if len(matches) == 1:
                    focus = matches.pop()
    elif error_focus in {"short_long_confusion", "madd_letter"}:
        focus = next((name for name in ("alif", "waw", "yaa") if name in evidence_type), "")
    else:
        focus = FOCUS_ALIASES.get(error_focus, "")
    if focus not in available:
        return None
    mapping = (support.get("focus_item_map") or {}).get(focus) or {}
    if len(mapping.get("check_ids") or []) != 2:
        return None
    return focus
