"""Owner-approved learner reading-text presentation policy (2026-09-21).

The historical content sources intentionally remain immutable migration inputs.
At the final release boundary, single letters/syllables/words keep their full
approved Arabic diacritics. Multi-word phrases, sentences, timed lists and
passages remove optional Arabic combining marks while retaining shadda (ّ),
which carries a consonant-doubling distinction important for reading.

The same projected text is used for learner-visible reading stimuli,
expected_reading_text and explicit reading-context introductions so display,
recording reference and exported training corpus cannot drift apart.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

SHADDA = "\u0651"
ARABIC_MARKS = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]")


def normalize_reading_text(value: str) -> str:
    """Keep single-token reading targets unchanged; simplify multi-word text."""
    text = str(value or "")
    if not re.search(r"\s", text.strip()):
        return text

    normalized = unicodedata.normalize("NFC", text)
    return ARABIC_MARKS.sub(lambda match: SHADDA if match.group(0) == SHADDA else "", normalized)


def apply_reading_text_policy(release: dict[str, Any]) -> None:
    """Project the approved reading-display rule onto one compiled release."""
    for item in release.get("items") or []:
        for step in item.get("rounds") or []:
            expected = step.get("expected_reading_text")
            if expected is not None:
                step["expected_reading_text"] = normalize_reading_text(str(expected))

            stimulus = step.get("stimulus")
            if isinstance(stimulus, dict) and stimulus.get("kind") == "reading" and stimulus.get("text") is not None:
                stimulus["text"] = normalize_reading_text(str(stimulus["text"]))

        intro = item.get("context_intro")
        if isinstance(intro, dict) and intro.get("kind") == "reading_context" and intro.get("text") is not None:
            intro["text"] = normalize_reading_text(str(intro["text"]))
