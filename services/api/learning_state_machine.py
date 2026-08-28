"""Pure policy primitives for the Himma learning journey.

This module deliberately contains no database mutations.  It is the canonical
M02 vocabulary used to separate activity outcome, mastery trend, and level
transition.  Runtime wiring is added incrementally so policy can be tested
without coupling it to persistence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ActivityOutcome = Literal["pass", "guided_retry", "reinforcement"]
JourneyOutcome = Literal["continue_level", "promote", "journey_complete"]

PASS_THRESHOLD = 80.0
GUIDED_RETRY_THRESHOLD = 70.0
LEVEL_MIN = 1
LEVEL_MAX = 3
CORE_ACTIVITIES_PER_LEVEL = 10


@dataclass(frozen=True)
class ActivityState:
    outcome: ActivityOutcome
    score: float
    reason: str


@dataclass(frozen=True)
class LevelState:
    outcome: JourneyOutcome
    current_level: int
    next_level: int | None
    reason: str


def classify_activity_score(score: float) -> ActivityState:
    """Classify one completed activity using the approved M02 boundaries.

    >=80 passes, 70..<80 receives a guided retry, and <70 creates a
    reinforcement need.  Values outside 0..100 are rejected rather than being
    silently clamped because they indicate a scoring defect upstream.
    """
    if score < 0 or score > 100:
        raise ValueError("activity score must be between 0 and 100")
    if score >= PASS_THRESHOLD:
        return ActivityState("pass", score, "activity_passed")
    if score >= GUIDED_RETRY_THRESHOLD:
        return ActivityState("guided_retry", score, "activity_needs_guided_retry")
    return ActivityState("reinforcement", score, "activity_below_70")


def level_completion_state(
    *,
    current_level: int,
    completed_core_count: int,
    unresolved_reinforcement: bool,
    required_skill_coverage_ok: bool,
    critical_skill_unresolved: bool,
) -> LevelState:
    """Return the deterministic journey state after evaluating level gates.

    This function does not use 50/30/20 mastery to skip core content.  Promotion
    requires all ten approved core activities plus clean reinforcement/skill
    gates.  L3 completion ends the learning journey; posttest availability is a
    separate study/supervisor policy.
    """
    if current_level < LEVEL_MIN or current_level > LEVEL_MAX:
        raise ValueError("current_level must be between 1 and 3")
    if completed_core_count < 0 or completed_core_count > CORE_ACTIVITIES_PER_LEVEL:
        raise ValueError("completed_core_count must be between 0 and 10")

    if completed_core_count < CORE_ACTIVITIES_PER_LEVEL:
        return LevelState("continue_level", current_level, current_level, "core_not_complete")
    if unresolved_reinforcement:
        return LevelState("continue_level", current_level, current_level, "reinforcement_pending")
    if not required_skill_coverage_ok:
        return LevelState("continue_level", current_level, current_level, "skill_coverage_pending")
    if critical_skill_unresolved:
        return LevelState("continue_level", current_level, current_level, "critical_skill_pending")

    if current_level == LEVEL_MAX:
        return LevelState("journey_complete", current_level, None, "level_three_complete")
    return LevelState("promote", current_level, current_level + 1, "level_complete")
