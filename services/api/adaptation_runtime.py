"""Runtime bridge between the durable Stage-2 activity session and P06 decisions.

Reinforcement and consolidation attempts intentionally share the durable ``core``
learning session. They are separate content kinds, so supervisor/core progress
continues to count only the ten approved core activities for the current level.
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
CORE_ACTIVITY_COUNT = 10


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


def _completed_core_count(db: Session, session_id: int, level_id: int) -> int:
    return (
        db.query(Attempt.id)
        .join(ContentItem, ContentItem.id == Attempt.item_id)
        .filter(
            Attempt.session_id == session_id,
            Attempt.status == "completed",
            ContentItem.kind == "core_activity",
            ContentItem.level_id == level_id,
        )
        .count()
    )


def _recommended_attempt_state(
    db: Session,
    session_id: int,
    item_id: int | None,
) -> str | None:
    """Return the durable state of the recommendation already attached to a decision.

    A completed reinforcement is a fulfilled recommendation, not a missing mapping.
    This distinction prevents a student from being blocked again immediately after
    completing the exact remedial activity that the adaptive engine assigned.
    """
    if item_id is None:
        return None
    attempt = db.query(Attempt).filter(
        Attempt.session_id == session_id,
        Attempt.item_id == item_id,
    ).first()
    return attempt.status if attempt else None


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
    allowed_levels = {decision.previous_level, decision.new_level}
    if item.level_id not in allowed_levels:
        raise HTTPException(status_code=409, detail="نشاط التوصية خارج انتقال المستوى المسموح")

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


def prepare_next_for_student(db: Session, student: Student, session: AssessmentSession) -> dict:
    """Evaluate the latest valid snapshot and prepare the next approved activity.

    The function is idempotent. Browser refreshes cannot duplicate a transition,
    and a completed reinforcement is remembered as fulfilled instead of becoming
    a false mapping gap on the next request.
    """
    decision_payload = evaluate_student(db, student)
    if not decision_payload.get("ready"):
        return {
            "continue_learning": session.status == "in_progress",
            "decision": decision_payload,
            "recommended_attempt_id": None,
            "mapping_blocked": False,
            "level_id": session.assigned_level,
        }

    decision = db.query(AdaptationDecision).filter(
        AdaptationDecision.id == decision_payload["decision_id"],
    ).one()

    old_session_level = session.assigned_level or decision.previous_level
    transitioned = decision.new_level != old_session_level
    if transitioned:
        session.assigned_level = decision.new_level
        session.status = "in_progress"
        session.completed_at = None
        session.updated_at = datetime.now(timezone.utc)

    recommendation_state_before = _recommended_attempt_state(
        db,
        session.id,
        decision.recommended_item_id,
    )
    attempt_id = _ensure_recommended_attempt(db, session, decision)
    recommendation_state_after = _recommended_attempt_state(
        db,
        session.id,
        decision.recommended_item_id,
    )
    recommendation_fulfilled = (
        recommendation_state_before == "completed"
        or recommendation_state_after == "completed"
    )

    if attempt_id is not None and session.status == "completed":
        session.status = "in_progress"
        session.completed_at = None
        session.updated_at = datetime.now(timezone.utc)

    level_for_progress = session.assigned_level or student.current_level
    core_complete = _completed_core_count(db, session.id, level_for_progress) >= CORE_ACTIVITY_COUNT
    mapping_blocked = (
        core_complete
        and decision.action in {"support", "stay"}
        and decision.explanation.get("reason") != "top_level_mastery"
        and attempt_id is None
        and not recommendation_fulfilled
    )
    if mapping_blocked:
        # Never substitute unrelated content merely to keep the flow moving.
        session.status = "in_progress"
        session.completed_at = None
        explanation = dict(decision.explanation or {})
        explanation["mapping_gap"] = "no_approved_reinforcement_selected_for_weakest_skill"
        decision.explanation = explanation
    elif recommendation_fulfilled:
        explanation = dict(decision.explanation or {})
        if explanation.pop("mapping_gap", None) is not None:
            explanation["mapping_gap_resolved"] = True
        explanation["reinforcement_fulfilled"] = True
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
        "recommendation_fulfilled": recommendation_fulfilled,
        "level_id": session.assigned_level,
    }


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
        raise HTTPException(status_code=404, detail="جلسة التعلم غير موجودة")
    return prepare_next_for_student(db, student, session)
