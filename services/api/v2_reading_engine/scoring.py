"""Reference-guided word alignment and owner-approved fractional scores.

Pure academic scoring: no external provider, storage or student mutation.
The caller must establish whether the audio is recognizable before scoring.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import unicodedata


_PASS_THRESHOLD = Decimal("0.85")
_FRACTION_UNIT = Decimal("0.00001")
_ALEF_EQUIVALENTS = str.maketrans({"إ": "ا", "أ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي"})


@dataclass(frozen=True)
class WordAlignment:
    kind: str
    reference: str | None
    observed: str | None


@dataclass(frozen=True)
class WordScore:
    target_words: int
    correct: int
    deletions: int
    substitutions: int
    insertions: int
    fraction: Decimal
    passed_assessment: bool
    fully_correct: bool
    alignment: tuple[WordAlignment, ...]


def _surface_words(text: str) -> list[str]:
    text = unicodedata.normalize("NFKC", text or "").replace("ـ", "")
    chars = []
    for ch in text:
        category = unicodedata.category(ch)
        chars.append(ch if ch.isalnum() or category.startswith("M") else " ")
    return [word for word in "".join(chars).split() if word]


def _normalized(word: str) -> str:
    value = "".join(ch for ch in word
                    if not unicodedata.category(ch).startswith("M"))
    return value.translate(_ALEF_EQUIVALENTS).casefold()


def align_words(reference: str, transcript: str) -> tuple[WordAlignment, ...]:
    ref = _surface_words(reference)
    observed = _surface_words(transcript)
    left = [_normalized(x) for x in ref]
    right = [_normalized(x) for x in observed]
    rows, cols = len(left) + 1, len(right) + 1
    costs = [[0] * cols for _ in range(rows)]
    actions = [[""] * cols for _ in range(rows)]

    for i in range(1, rows):
        costs[i][0], actions[i][0] = i, "deletion"
    for j in range(1, cols):
        costs[0][j], actions[0][j] = j, "insertion"

    for i in range(1, rows):
        for j in range(1, cols):
            same = left[i - 1] == right[j - 1]
            options = (
                (costs[i - 1][j - 1] + (0 if same else 1),
                 "correct" if same else "substitution"),
                (costs[i - 1][j] + 1, "deletion"),
                (costs[i][j - 1] + 1, "insertion"),
            )
            costs[i][j], actions[i][j] = min(options, key=lambda p: p[0])

    alignment = []
    i, j = len(left), len(right)
    while i or j:
        operation = actions[i][j]
        if operation in {"correct", "substitution"}:
            alignment.append(WordAlignment(operation, ref[i - 1], observed[j - 1]))
            i -= 1
            j -= 1
        elif operation == "deletion":
            alignment.append(WordAlignment(operation, ref[i - 1], None))
            i -= 1
        elif operation == "insertion":
            alignment.append(WordAlignment(operation, None, observed[j - 1]))
            j -= 1
        else:
            raise RuntimeError("Incomplete reading alignment")
    return tuple(reversed(alignment))


def grade_words(reference: str, transcript: str) -> WordScore:
    """Each required word has equal weight; extras deduct the same weight.

    N = C + D + S; fraction = max(0, C - I) / N.
    >85% means an assessment *pass* (exact 85% does not).
    """
    alignment = align_words(reference, transcript)
    counts = {kind: sum(row.kind == kind for row in alignment)
              for kind in ("correct", "deletion", "substitution", "insertion")}
    target = counts["correct"] + counts["deletion"] + counts["substitution"]
    if target == 0:
        raise ValueError("Cannot grade an empty reference")
    numerator = max(0, counts["correct"] - counts["insertion"])
    fraction = (Decimal(numerator) / Decimal(target)).quantize(
        _FRACTION_UNIT, rounding=ROUND_HALF_UP)
    fully_correct = (counts["correct"] == target
                     and counts["deletion"] == counts["substitution"]
                     == counts["insertion"] == 0)
    return WordScore(
        target_words=target,
        correct=counts["correct"],
        deletions=counts["deletion"],
        substitutions=counts["substitution"],
        insertions=counts["insertion"],
        fraction=fraction,
        passed_assessment=fraction > _PASS_THRESHOLD,
        fully_correct=fully_correct,
        alignment=alignment,
    )


def training_hint(score: WordScore) -> str | None:
    """One short user-facing sentence identifying an actual word error."""
    for row in score.alignment:
        if row.kind == "deletion":
            return f"اقتربت! نسيت كلمة «{row.reference}». اقرأ العبارة مرة أخرى."
        if row.kind == "insertion":
            return f"قراءة جميلة! زدت كلمة «{row.observed}». اقرأ المكتوب فقط."
        if row.kind == "substitution":
            return f"اقتربت! أعد قراءة كلمة «{row.reference}» وحاول مرة ثانية."
    return None


def assessment_total(question_fractions: list[Decimal]) -> Decimal:
    """Exactly 30 completed questions of equal weight, never binary pass count."""
    if len(question_fractions) != 30:
        raise ValueError("All 30 questions must be graded before final scoring")
    if any(not frac.is_finite() or frac < 0 or frac > 1
           for frac in question_fractions):
        raise ValueError("Question fraction must be finite and within 0..1")
    return (sum(question_fractions, Decimal("0")) * Decimal("100") /
            Decimal("30")).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
