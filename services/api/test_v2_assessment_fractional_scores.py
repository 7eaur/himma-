"""Owner-approved fractional grade contract for 30-question V2 assessments."""
from decimal import Decimal
from types import SimpleNamespace as Row

import pytest

from v2_reading_engine.assessment_scores import summarize_assessment


def row(*, status="graded", correct=True, fraction=None, skill="reading"):
    return Row(status=status, is_correct=correct, question_score_fraction=fraction,
               skill_group=skill)


def test_legacy_binary_assessment_remains_100_without_fraction():
    result = summarize_assessment([row() for _ in range(30)])
    assert result["answered"] == 30
    assert result["correct"] == 30
    assert result["score_percent"] == 100.0


def test_partial_pass_keeps_real_fraction_in_total():
    values = [row() for _ in range(29)] + [row(fraction=Decimal("0.85714"))]
    result = summarize_assessment(values)
    assert result["correct"] == 30
    assert result["score_percent"] == 99.5238


def test_85_percent_failed_question_retains_85_percent_credit():
    values = [row() for _ in range(29)] + [
        row(correct=False, fraction=Decimal("0.85000")),
    ]
    result = summarize_assessment(values)
    assert result["correct"] == 29
    assert result["score_percent"] == 99.5


def test_pending_neutral_reading_cannot_generate_total():
    values = [row() for _ in range(29)] + [
        row(status="pending_review", correct=None),
    ]
    result = summarize_assessment(values)
    assert result["pending_review"] == 1
    assert result["score_percent"] is None
    assert result["correct"] is None
    assert result["skills"]["reading"] == {
        "graded": 29, "correct": 29, "pending": 1,
    }


def test_gradeless_submitted_response_is_not_implicitly_zero():
    values = [row() for _ in range(29)] + [row(correct=None, fraction=None)]
    result = summarize_assessment(values)
    assert result["pending_review"] == 1
    assert result["score_percent"] is None


def test_partial_objective_results_do_not_finalize():
    result = summarize_assessment([row() for _ in range(29)])
    assert result["score_percent"] is None


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-0.01", "1.01"])
def test_invalid_fraction_cannot_be_used_for_placement(value):
    values = [row() for _ in range(29)] + [
        row(fraction=value),
    ]
    with pytest.raises(ValueError):
        summarize_assessment(values)


def test_duplicate_or_more_than_30_rows_rejected():
    with pytest.raises(ValueError):
        summarize_assessment([row() for _ in range(31)])


def test_mixed_skills_preserve_existing_shape():
    values = [row(skill="letters") for _ in range(10)] + [
        row(correct=False, fraction=Decimal("0.50000"), skill="sentence")
        for _ in range(20)
    ]
    result = summarize_assessment(values)
    assert result["score_percent"] == 66.6667
    assert result["skills"]["letters"]["correct"] == 10
    assert result["skills"]["sentence"]["correct"] == 0



def test_fraction_without_verified_correctness_cannot_complete_assessment():
    # A broken handoff may have a numeric fraction before the academic
    # decision is applied. The score must remain neutral and unplaceable.
    entries = [row(skill="letters") for _ in range(29)] + [
        row(status="graded", correct=None, fraction=Decimal("0.85714"),
            skill="sentence")
    ]
    result = summarize_assessment(entries)
    assert result["answered"] == 30
    assert result["pending_review"] == 1
    assert result["correct"] is None
    assert result["score_percent"] is None
    assert result["skills"]["sentence"]["pending"] == 1


@pytest.mark.parametrize("correct_count,level,score", [
    (0, 1, 0.0),
    (14, 1, 46.6667),
    (15, 2, 50.0),
    (23, 2, 76.6667),
    (24, 3, 80.0),
    (30, 3, 100.0),
])
def test_exactly_30_graded_items_preserve_placement_bands(correct_count, level, score):
    # This uses the same percentages consumed by the official 50/80
    # placement policy, without requiring a runtime database or Azure.
    answer_rows = [row(correct=True) for _ in range(correct_count)]
    answer_rows += [row(correct=False) for _ in range(30 - correct_count)]
    total = summarize_assessment(answer_rows)
    assert total["score_percent"] == score
    computed_level = 1 if score < 50 else 2 if score < 80 else 3
    assert computed_level == level
    assert total["correct"] == correct_count


def test_partial_reading_fraction_affects_placement_not_binary_pass_count():
    # 14 normal correct questions + one 85.714% reading + 15 wrong
    # questions produces 49.5238% (L1), NOT 15/30=50% (L2).
    rows = [row(correct=True) for _ in range(14)]
    rows += [row(correct=True, fraction=Decimal("0.85714"), skill="sentence")]
    rows += [row(correct=False) for _ in range(15)]
    score = summarize_assessment(rows)
    assert score["correct"] == 15
    assert score["score_percent"] == 49.5238
    assert score["score_percent"] < 50


def test_no_recognition_never_creates_partial_score_or_placement():
    rows = [row(correct=True) for _ in range(29)]
    rows += [row(status="pending_review", correct=None, fraction=None)]
    result = summarize_assessment(rows)
    assert result["answered"] == 30
    assert result["pending_review"] == 1
    assert result["score_percent"] is None
