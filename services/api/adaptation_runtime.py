"""Runtime bridge between the durable Stage-2 activity session and P06 decisions.

Reinforcement and consolidation attempts intentionally share the durable `core`
learning session. They are separate content kinds, so researcher/core progress
continues to count only the ten approved core activities for the *current* level.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from adaptation import evaluate_student
from db.adaptation_models import AdaptationDecision
from db.models import AssessmentSession, Attempt, ContentItem, Student
from dependencies import get_current_student, get_db

router = APIRouter(prefix="/adaptation", tags=["Adaptation Runtime"])


def _first_consolidation_item(db: Session, level_id: int) -> ContentItem | None:
    return (
        db.query(ContentItem)
        .filter(
            ContentItem.kind == "core_activity",
            ContentItem.level_id == level_id,
        )
        .order_by(ContentItem.order_index)
        .first()
    )


def _ensure_recommended_attempt(
    db: Session,
    session: AssessmentSession,
    decision: AdaptationDecision,
) -> int | None:
    item_id = decision.recommended_item_id
    if decision.action == "promote" and item_id is None:
        consolidation = _first_consolidation_item(db, decision.new_level)
        if consolidation:
            item_id = consolidation.id
            decision.recommended_item_id = item_id
            explanation = dict(decision.explanation or {})
            explanation["consolidation_assignment"] = "first_approved_core_activity_of_new_level"
            decision.explanation = explanation

    if item_id is None:
        return None

    item = db.query(ContentItem).filter(ContentItem.id == item_id).first()
    if not item:
        return None
    # A recommendation is only allowed inside the level it was selected for.
    allowed_levels = {decision.previous_level, decision.new_level}
    if item.level_id not in allowed_levels:
        raise HTTPException(status_code=409, detail="Adaptive recommendation is outside the allowed level transition")

    existing = db.query(Attempt).filter(
        Attempt.session_id == session.id,
        Attempt.item_id == item.id,
    ).first()
    if existing:
        return existing.id if existing.status == "in_progress" else None

    attempt = Attempt(session_id=session.id, item_id=item.id, status="in_progress")
    db.add(attempt)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        existing = db.query(Attempt).filter(
            Attempt.session_id == session.id,
            Attempt.item_id == item.id,
        ).first()
        return existing.id if existing and existing.status == "in_progress" else None
    return attempt.id


@router.post("/session/{session_id}/prepare-next")
def prepare_adaptive_next(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.student_id == student.id,
        AssessmentSession.session_type == "core",
    ).with_for_update().first()
    if not session:
        raise HTTPException(status_code=404, detail="Learning session not found")

    decision_payload = evaluate_student(db, student)
    if not decision_payload.get("ready"):
        return {
            "continue_learning": session.status == "in_progress",
            "decision": decision_payload,
            "recommended_attempt_id": None,
        }

    decision = db.query(AdaptationDecision).filter(
        AdaptationDecision.id == decision_payload["decision_id"],
    ).one()

    transitioned = decision.new_level != (session.assigned_level or decision.previous_level)
    if transitioned:
        session.assigned_level = decision.new_level
        # A level transition continues the intervention rather than falsely
        # unlocking the posttest from the just-finished previous-level core set.
        session.status = "in_progress"
        session.completed_at = None
        session.updated_at = datetime.now(timezone.utc)

    attempt_id = _ensure_recommended_attempt(db, session, decision)
    if attempt_id is not None and session.status == "completed":
        # Support/consolidation must be completed before the learning session is
        # allowed to remain academically complete.
        session.status = "in_progress"
        session.completed_at = None
        session.updated_at = datetime.now(timezone.utc)

    # If all ten core activities completed but the approved decision calls for
    # support/stability and there is no exact skill-matched reinforcement left,
    # do not invent content. Record the mapping gap and keep the researcher in
    # control instead of silently opening the posttest.
    mapping_blocked = (
        session.status == "completed"
        and decision.action in {"support", "stay"}
        and decision.explanation.get("reason") != "top_level_mastery"
        and attempt_id is None
    )
    if mapping_blocked:
        session.status = "in_progress"
        session.completed_at = None
        explanation = dict(decision.explanation or {})
        explanation["mapping_gap"] = "no_unused_exact_skill_reinforcement"
        decision.explanation = explanation

    db.commit()
    return {
        "continue_learning": session.status == "in_progress",
        "decision": {
            **decision_payload,
            "recommended_item_id": decision.recommended_item_id,
            "explanation": decision.explanation,
        },
        "recommended_attempt_id": attempt_id,
        "mapping_blocked": mapping_blocked,
        "level_id": session.assigned_level,
    }
