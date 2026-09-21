"""Minimal, conservative decision preview for Himma Speech Lab.

The production policy is intentionally not invented here. Lexical tasks have a
deterministic word-alignment decision. Targeted pronunciation and fluency stay
retry-required until real provider evidence / content timing policy are tested.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

DecisionState = Literal["correct", "incorrect", "retry_required"]


@dataclass(frozen=True)
class SpeechDecision:
    state: DecisionState
    reason: str


def preview_speech_decision(
    *,
    mode: str,
    counts: dict[str, int],
    alias_matched: bool = False,
) -> SpeechDecision:
    errors = (
        int(counts.get("deletion", 0))
        + int(counts.get("insertion", 0))
        + int(counts.get("substitution", 0))
    )

    if mode == "lexical":
        if errors == 0:
            return SpeechDecision("correct", "exact_lexical_match")
        return SpeechDecision("incorrect", "lexical_mismatch")

    if mode == "targeted_pronunciation":
        if alias_matched:
            return SpeechDecision("retry_required", "asr_alias_requires_pronunciation_evidence")
        return SpeechDecision("retry_required", "pronunciation_evidence_required")

    if mode == "fluency":
        return SpeechDecision("retry_required", "fluency_timing_policy_pending")

    return SpeechDecision("retry_required", "unclassified_speech_task")
