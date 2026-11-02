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
