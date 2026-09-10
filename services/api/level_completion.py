"""Canonical level-completion evidence for journey, rewards and admin views.

A learner's ``current_level`` is a pointer, not proof that every lower level was
academically completed. Completion is derived from the durable Core session and
its persisted evidence:

- any level is complete after all ten Core activities in a completed session;
- L1/L2 may also complete through the approved automatic early-promotion event;
- L3 never uses early promotion and still requires all ten Core activities;
- manual level overrides do not fabricate completion evidence.

Consumers should reuse this module instead of re-inferring completion from the
student's current level or inventing a separate 10/10-only badge rule.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from db.adaptation_models import AdaptationDecision
from db.models import AssessmentSession, Attempt, ContentItem

CORE_ACTIVITY_COUNT = 10


@dataclass(frozen=True)
class LevelCompletionEvidence:
    completed: bool
    completed_core_count: int
    method: str | None = None
    promotion_decision_id: int | None = None


def completed_core_count(db: Session, session_id: int, level_id: int) -> int:
    rows = (
        db.query(ContentItem.id)
        .join(Attempt, Attempt.item_id == ContentItem.id)
        .filter(
            Attempt.session_id == session_id,
            Attempt.status == "completed",
            ContentItem.kind == "core_activity",
            ContentItem.level_id == level_id,
        )
        .distinct()
        .all()
    )
    return len(rows)


def _automatic_promotion_for_session(
    db: Session,
    session: AssessmentSession,
) -> AdaptationDecision | None:
    level_id = int(session.assigned_level or 0)
    if level_id not in {1, 2}:
        return None
    decisions = (
        db.query(AdaptationDecision)
        .filter(
            AdaptationDecision.student_id == session.student_id,
            AdaptationDecision.decision_source == "automatic",
            AdaptationDecision.action == "promote",
            AdaptationDecision.previous_level == level_id,
            AdaptationDecision.new_level == level_id + 1,
        )
        .order_by(AdaptationDecision.id.desc())
        .all()
    )
    expected_transition = f"L{level_id}->L{level_id + 1}"
    for decision in decisions:
        explanation = decision.explanation or {}
        if (
            explanation.get("previous_session_id") == session.id
            and explanation.get("journey_transition") == expected_transition
        ):
            return decision
    return None


def session_level_completion(
    db: Session,
    session: AssessmentSession,
) -> LevelCompletionEvidence:
    """Evaluate durable completion evidence for one Core session."""
    level_id = int(session.assigned_level or 0)
    if session.session_type != "core" or level_id not in {1, 2, 3}:
        return LevelCompletionEvidence(False, 0)

    count = completed_core_count(db, session.id, level_id)
    if session.status != "completed":
        return LevelCompletionEvidence(False, count)
    if count >= CORE_ACTIVITY_COUNT:
        return LevelCompletionEvidence(True, count, method="full_core")

    promotion = _automatic_promotion_for_session(db, session)
    if promotion is not None:
        return LevelCompletionEvidence(
            True,
            count,
            method="early_promotion",
            promotion_decision_id=promotion.id,
        )
    return LevelCompletionEvidence(False, count)


def completed_level_sessions(
    db: Session,
    student_id: int,
    level_id: int,
) -> list[tuple[AssessmentSession, LevelCompletionEvidence]]:
    """Return completed-evidence sessions in durable chronological order."""
    sessions = (
        db.query(AssessmentSession)
        .filter(
            AssessmentSession.student_id == student_id,
            AssessmentSession.session_type == "core",
            AssessmentSession.assigned_level == level_id,
        )
        .order_by(AssessmentSession.id)
        .all()
    )
    result: list[tuple[AssessmentSession, LevelCompletionEvidence]] = []
    for session in sessions:
        evidence = session_level_completion(db, session)
        if evidence.completed:
            result.append((session, evidence))
    return result


def level_was_completed(db: Session, student_id: int, level_id: int) -> bool:
    return bool(completed_level_sessions(db, student_id, level_id))
