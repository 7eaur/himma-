import pytest

from learning_state_machine import classify_activity_score, level_completion_state


@pytest.mark.parametrize(
    ("score", "outcome"),
    [
        (100, "pass"),
        (80, "pass"),
        (79.9999, "guided_retry"),
        (70, "guided_retry"),
        (69.9999, "reinforcement"),
        (0, "reinforcement"),
    ],
)
def test_activity_state_boundaries(score, outcome):
    assert classify_activity_score(score).outcome == outcome


@pytest.mark.parametrize("score", [-0.01, 100.01])
def test_activity_state_rejects_invalid_score(score):
    with pytest.raises(ValueError):
        classify_activity_score(score)


def test_level_cannot_promote_before_ten_core_activities():
    state = level_completion_state(
        current_level=1,
        completed_core_count=9,
        unresolved_reinforcement=False,
        required_skill_coverage_ok=True,
        critical_skill_unresolved=False,
    )
    assert state.outcome == "continue_level"
    assert state.next_level == 1


def test_level_completion_waits_for_reinforcement_and_skill_gates():
    reinforcement = level_completion_state(
        current_level=2,
        completed_core_count=10,
        unresolved_reinforcement=True,
        required_skill_coverage_ok=True,
        critical_skill_unresolved=False,
    )
    assert reinforcement.outcome == "continue_level"
    assert reinforcement.reason == "reinforcement_pending"

    coverage = level_completion_state(
        current_level=2,
        completed_core_count=10,
        unresolved_reinforcement=False,
        required_skill_coverage_ok=False,
        critical_skill_unresolved=False,
    )
    assert coverage.outcome == "continue_level"
    assert coverage.reason == "skill_coverage_pending"

    critical = level_completion_state(
        current_level=2,
        completed_core_count=10,
        unresolved_reinforcement=False,
        required_skill_coverage_ok=True,
        critical_skill_unresolved=True,
    )
    assert critical.outcome == "continue_level"
    assert critical.reason == "critical_skill_pending"


def test_level_one_and_two_promote_only_one_level():
    first = level_completion_state(
        current_level=1,
        completed_core_count=10,
        unresolved_reinforcement=False,
        required_skill_coverage_ok=True,
        critical_skill_unresolved=False,
    )
    second = level_completion_state(
        current_level=2,
        completed_core_count=10,
        unresolved_reinforcement=False,
        required_skill_coverage_ok=True,
        critical_skill_unresolved=False,
    )
    assert (first.outcome, first.next_level) == ("promote", 2)
    assert (second.outcome, second.next_level) == ("promote", 3)


def test_level_three_completion_ends_journey_without_fake_level_four():
    state = level_completion_state(
        current_level=3,
        completed_core_count=10,
        unresolved_reinforcement=False,
        required_skill_coverage_ok=True,
        critical_skill_unresolved=False,
    )
    assert state.outcome == "journey_complete"
    assert state.next_level is None
