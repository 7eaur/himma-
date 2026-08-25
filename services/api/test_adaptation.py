"""P06 adaptive engine boundary and invariance tests."""

import pytest

from adaptation import decide_transition, weighted_mastery
from db.database import SessionLocal
from db.adaptation_models import AdaptationDecision
from db.models import Student


@pytest.mark.parametrize(
    ("scores", "expected"),
    [
        ([100, 100, 100], 100.0),
        ([0, 0, 0], 0.0),
        ([100, 0, 0], 50.0),
        ([0, 100, 0], 30.0),
        ([0, 0, 100], 20.0),
        ([80, 70, 60], 73.0),
    ],
)
def test_weighted_mastery_uses_50_30_20_newest_first(scores, expected):
    assert weighted_mastery(scores) == expected


def test_weighted_mastery_stays_inside_input_range_and_is_monotonic_for_newest():
    for oldest in range(0, 101, 10):
        for previous in range(0, 101, 10):
            low = weighted_mastery([20, previous, oldest])
            high = weighted_mastery([80, previous, oldest])
            assert low <= high
            for value in (low, high):
                assert min(20, 80, previous, oldest) <= value <= max(20, 80, previous, oldest)


@pytest.mark.parametrize(
    ("mastery", "action"),
    [(49.9999, "support"), (50.0, "stay"), (79.9999, "stay")],
)
def test_transition_threshold_boundaries(mastery, action):
    result, level, _ = decide_transition(
        current_level=2,
        mastery=mastery,
        skill_coverage_ok=True,
        minimum_required_skill_score=100,
        previous_low=False,
    )
    assert result == action
    assert level == 2


def test_promotion_requires_80_coverage_and_skill_floor():
    assert decide_transition(
        current_level=1,
        mastery=80,
        skill_coverage_ok=True,
        minimum_required_skill_score=60,
        previous_low=False,
    )[0:2] == ("promote", 2)

    assert decide_transition(
        current_level=1,
        mastery=99,
        skill_coverage_ok=False,
        minimum_required_skill_score=100,
        previous_low=False,
    )[0] == "stay"

    assert decide_transition(
        current_level=1,
        mastery=99,
        skill_coverage_ok=True,
        minimum_required_skill_score=59.9999,
        previous_low=False,
    )[0] == "stay"


def test_low_mastery_supports_before_demoting_and_never_below_one():
    assert decide_transition(
        current_level=2,
        mastery=40,
        skill_coverage_ok=True,
        minimum_required_skill_score=40,
        previous_low=False,
    )[0:2] == ("support", 2)
    assert decide_transition(
        current_level=2,
        mastery=40,
        skill_coverage_ok=True,
        minimum_required_skill_score=40,
        previous_low=True,
    )[0:2] == ("demote", 1)
    assert decide_transition(
        current_level=1,
        mastery=40,
        skill_coverage_ok=True,
        minimum_required_skill_score=40,
        previous_low=True,
    )[0:2] == ("support", 1)


def test_top_level_does_not_promote_above_three():
    assert decide_transition(
        current_level=3,
        mastery=100,
        skill_coverage_ok=True,
        minimum_required_skill_score=100,
        previous_low=False,
    )[0:2] == ("stay", 3)


def test_manual_override_requires_reason_and_preserves_history(researcher_client):
    db = SessionLocal()
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    student_id = student.id
    db.add(AdaptationDecision(
        student_id=student.id,
        decision_source="automatic",
        action="stay",
        mastery_score=75,
        previous_level=1,
        new_level=1,
        valid_attempt_count=3,
        consecutive_low_count=0,
        snapshot_key="1:2:3",
        explanation={"reason": "test-history"},
    ))
    db.commit()
    db.close()

    invalid = researcher_client.post(
        f"/researcher/students/{student_id}/adaptation/manual-override",
        json={"new_level": 2, "reason": "لا"},
    )
    assert invalid.status_code == 422

    override = researcher_client.post(
        f"/researcher/students/{student_id}/adaptation/manual-override",
        json={"new_level": 2, "reason": "قرار بحثي موثق للاختبار"},
    )
    assert override.status_code == 200
    assert override.json()["source"] == "manual"
    assert override.json()["previous_level"] == 1
    assert override.json()["new_level"] == 2

    history = researcher_client.get(f"/researcher/students/{student_id}/adaptation/history")
    assert history.status_code == 200
    assert [row["source"] for row in history.json()] == ["automatic", "manual"]
