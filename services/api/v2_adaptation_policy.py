"""Pure, versioned P05 policy for V2 evidence and targeted support.

The policy deliberately avoids V1 score thresholds. A clean independent
check advances, one mapped gap requests a short alternate check, and repeated
evidence for the same mapped focus opens targeted support. Unmapped authoring
terms fail closed to supervisor review instead of guessing a remediation.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Literal

from v2_content.adaptation_mapping import resolve_question_focus
from v2_content.repository import get_support_for_lesson


POLICY_VERSION = "himma-v2-adaptation/1-candidate"

DecisionKind = Literal[
    "next_lesson",
    "additional_check",
    "targeted_support",
    "waiting_review",
    "supervisor_hold",
]


@dataclass(frozen=True)
class EvidenceSignal:
    evidence_id: int
    question_id: str
    lesson_id: str
    skill_group: str
    evidence_type: str
    error_focus: str | None
    is_correct: bool | None
    review_status: str


@dataclass(frozen=True)
class PolicyDecision:
    kind: DecisionKind
    reason_code: str
    evidence_ids: tuple[int, ...]
    support_id: str | None = None
    focus: str | None = None


def resolve_focus(question: dict[str, Any]) -> tuple[str, str] | None:
    """Return an approved support/focus pair or an explicit mapping gap."""
    lesson_id = str(question.get("owner_id") or "")
    support = get_support_for_lesson(lesson_id)
    if not support:
        return None
    focus = resolve_question_focus(question, support)
    if not focus:
        return None
    return support["id"], focus


def evaluate_independent(signals: list[EvidenceSignal], questions: dict[str, dict[str, Any]]) -> PolicyDecision:
    pending = [row for row in signals if row.review_status == "pending_review" or row.is_correct is None]
    if pending:
        return PolicyDecision(
            kind="waiting_review",
            reason_code="independent_evidence_pending_human_review",
            evidence_ids=tuple(row.evidence_id for row in pending),
        )

    incorrect = [row for row in signals if row.is_correct is False]
    if not incorrect:
        return PolicyDecision(
            kind="next_lesson",
            reason_code="independent_evidence_stable",
            evidence_ids=tuple(row.evidence_id for row in signals),
        )

    mapped: list[tuple[EvidenceSignal, str, str]] = []
    unmapped: list[EvidenceSignal] = []
    for row in incorrect:
        resolved = resolve_focus(questions[row.question_id])
        if resolved:
            mapped.append((row, resolved[0], resolved[1]))
        else:
            unmapped.append(row)
    if unmapped:
        return PolicyDecision(
            kind="supervisor_hold",
            reason_code="authoring_focus_mapping_missing",
            evidence_ids=tuple(row.evidence_id for row in unmapped),
        )

    counts = Counter((support_id, focus) for _, support_id, focus in mapped)
    chosen = next((key for key, count in counts.items() if count >= 2), None)
    kind: DecisionKind = "targeted_support" if chosen else "additional_check"
    chosen = chosen or (mapped[0][1], mapped[0][2])
    selected = tuple(row.evidence_id for row, support_id, focus in mapped if (support_id, focus) == chosen)
    return PolicyDecision(
        kind=kind,
        reason_code="repeated_focus_gap" if kind == "targeted_support" else "single_gap_needs_alternate_check",
        evidence_ids=selected,
        support_id=chosen[0],
        focus=chosen[1],
    )


def evaluate_support(signals: list[EvidenceSignal], *, was_additional_check: bool) -> PolicyDecision:
    pending = [row for row in signals if row.review_status == "pending_review" or row.is_correct is None]
    if pending:
        return PolicyDecision(
            kind="waiting_review",
            reason_code="support_evidence_pending_human_review",
            evidence_ids=tuple(row.evidence_id for row in pending),
        )
    if signals and all(row.is_correct is True for row in signals):
        return PolicyDecision(
            kind="next_lesson",
            reason_code="alternate_check_resolved_gap" if was_additional_check else "support_check_resolved_gap",
            evidence_ids=tuple(row.evidence_id for row in signals),
        )
    return PolicyDecision(
        kind="targeted_support" if was_additional_check else "supervisor_hold",
        reason_code="alternate_check_confirmed_gap" if was_additional_check else "support_attempt_limit_reached",
        evidence_ids=tuple(row.evidence_id for row in signals),
    )
