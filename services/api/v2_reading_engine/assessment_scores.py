"""Single V2 assessment aggregation contract for objective and reading scores.

Historical objective/human-graded rows without question_score_fraction retain
their previous 0/1 meaning. New native reading rows keep partial word credit.
"""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any, Iterable

from .scoring import assessment_total


def summarize_assessment(rows: Iterable[Any], *, total: int = 30) -> dict[str, Any]:
    if total != 30:
        raise ValueError("V2 assessment requires exactly 30 equal-weight questions")
    entries = list(rows)
    if len(entries) > total:
        raise ValueError("Unexpected extra assessment responses")
    pending = 0
    correct_count = 0
    earned: list[Decimal] = []
    skills: dict[str, dict[str, int]] = defaultdict(
        lambda: {"graded": 0, "correct": 0, "pending": 0},
    )
    for row in entries:
        label = str(row.skill_group)
        section = skills[label]
        fraction = getattr(row, "question_score_fraction", None)
        # An imported/legacy "graded" marker or a fractional value alone
        # is NOT verified academic evidence. A native reading result must
        # include the final correctness decision and fraction together.
        # Keep incomplete rows neutral: never turn them into scores or level
        # placement while a child's recording is awaiting evaluation.
        if row.status != "graded" or not isinstance(row.is_correct, bool):
            pending += 1
            section["pending"] += 1
            continue
        if fraction is None:
            fraction = Decimal(1 if row.is_correct is True else 0)
        else:
            fraction = Decimal(str(fraction))
        if not fraction.is_finite() or fraction < 0 or fraction > 1:
            raise ValueError("Invalid academic fraction in assessment response")
        earned.append(fraction)
        section["graded"] += 1
        if row.is_correct is True:
            section["correct"] += 1
            correct_count += 1

    complete = len(entries) == total and pending == 0 and len(earned) == total
    return {
        "answered": len(entries),
        "total": total,
        "pending_review": pending,  # Historical API compatibility; retired at full cutover.
        "correct": correct_count if complete else None,
        "score_percent": float(assessment_total(earned)) if complete else None,
        "skills": dict(sorted(skills.items())),
    }
