"""Runtime bridge for the upward Himma learning journey.

Each level now owns a durable ``core`` session. Completing L1 closes that session
and opens a new L2 session; completing L2 does the same for L3. Historical
sessions are never relabelled. Reinforcement remains inside the current level
and a missing safe mapping blocks progression rather than selecting unrelated
content.
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


def _recommended_attempt_state(db: Session, session_id: int, item_id: int | None) -> str | None:
    if item_id is None:
        return None
    attempt = (
        db.query(Attempt)
        .filter(Attempt.session_id == session_id, Attempt.item_id == item_id)
        .order_by(Attempt.id.desc())
        .first()
    )
    return attempt.status if attempt else None


def _ensure_recommended_attempt(
    db: Session,
    session: AssessmentSession,
    decision: AdaptationDecision,
) -> int | None:
    """Create only the explicitly mapped reinforcement attempt.

    Promotion no longer injects a consolidation activity into the old session;
    the next level receives its own session and starts naturally at activity 1.
    """
    item_id = decision.recommended_item_id
    if item_id is None or decision.action != "support":
        return None

    item = db.query(ContentItem).filter(ContentItem.id == item_id).first()
    if not item:
        return None
    if item.kind != "reinforcement_activity" or item.level_id != decision.previous_level:
        raise HTTPException(status_code=409, detail="نشاط التقوية لا يطابق المستوى الحالي")

    existing = (
        db.query(Attempt)
        .filter(Attempt.session_id == session.id, Attempt.item_id == item.id)
        .order_by(Attempt.id.desc())
        .first()
    )
    if existing:
        return existing.id if existing.status == "in_progress" else None

    attempt = Attempt(session_id=session.id, item_id=item.id, status="in_progress")
    try:
        with db.begin_nested():
            db.add(attempt)
            db.flush()
    except IntegrityError:
        existing = (
            db.query(Attempt)
            .filter(Attempt.session_id == session.id, Attempt.item_id == item.id)
            .order_by(Attempt.id.desc())
            .first()
        )
        return existing.id if existing and existing.status == "in_progress" else None
    return attempt.id


def _open_next_level_session(
    db: Session,
    student: Student,
    old_session: AssessmentSession,
    new_level: int,
) -> AssessmentSession:
    """Close one level and create the next without rewriting history."""
    now = datetime.now(timezone.utc)
    old_session.status = "completed"
    old_session.completed_at = old_session.completed_at or now
    old_session.updated_at = now
    db.flush()  # release the partial unique active-session index

    existing = (
        db.query(AssessmentSession)
        .filter(
            AssessmentSession.student_id == student.id,
            AssessmentSession.session_type == "core",
            AssessmentSession.assigned_level == new_level,
        )
        .order_by(AssessmentSession.id.desc())
        .first()
    )
    if existing:
        if existing.status != "in_progress":
            # A completed historical next-level session means the student has
            # already traversed this level; never erase it or silently reopen it.
            return existing
        student.current_level = new_level
        return existing

    next_session = AssessmentSession(
        student_id=student.id,
        session_type="core",
        status="in_progress",
        assigned_level=new_level,
    )
    db.add(next_session)
    student.current_level = new_level
    db.flush()
    return next_session


def prepare_next_for_student(db: Session, student: Student, session: AssessmentSession) -> dict:
    """Evaluate the latest evidence and prepare the next safe learning action."""
    decision_payload = evaluate_student(db, student)
    if not decision_payload.get("ready"):
        return {
            "continue_learning": session.status == "in_progress",
            "decision": decision_payload,
            "recommended_attempt_id": None,
            "mapping_blocked": False,
            "recommendation_fulfilled": False,
            "level_id": session.assigned_level,
            "session_id": session.id,
        }

    decision = db.query(AdaptationDecision).filter(
        AdaptationDecision.id == decision_payload["decision_id"],
    ).one()

    # A promotion is a level-boundary operation, never a relabel of the old
    # session. This gives reports a trustworthy L1/L2/L3 history.
    if decision.action == "promote" and decision.new_level > decision.previous_level:
        next_session = _open_next_level_session(db, student, session, decision.new_level)
        explanation = dict(decision.explanation or {})
        explanation["journey_transition"] = f"L{decision.previous_level}->L{decision.new_level}"
        explanation["previous_session_id"] = session.id
        explanation["next_session_id"] = next_session.id
        decision.explanation = explanation
        db.commit()
        return {
            "continue_learning": next_session.status == "in_progress",
            "decision": {**decision_payload, "explanation": decision.explanation},
            "recommended_attempt_id": None,
            "mapping_blocked": False,
            "recommendation_fulfilled": False,
            "level_id": decision.new_level,
            "session_id": next_session.id,
            "level_transitioned": True,
        }

    # L3 completion ends the intervention journey. The posttest is enabled only
    # by its separate supervisor/eligibility policy.
    if (
        decision.previous_level == 3
        and decision.explanation.get("reason") == "top_level_completed"
        and _completed_core_count(db, session.id, 3) >= CORE_ACTIVITY_COUNT
    ):
        now = datetime.now(timezone.utc)
        session.status = "completed"
        session.completed_at = session.completed_at or now
        session.updated_at = now
        db.commit()
        return {
            "continue_learning": False,
            "decision": decision_payload,
            "recommended_attempt_id": None,
            "mapping_blocked": False,
            "recommendation_fulfilled": False,
            "level_id": 3,
            "session_id": session.id,
            "journey_completed": True,
        }

    recommendation_state_before = _recommended_attempt_state(db, session.id, decision.recommended_item_id)
    attempt_id = _ensure_recommended_attempt(db, session, decision)
    recommendation_state_after = _recommended_attempt_state(db, session.id, decision.recommended_item_id)
    recommendation_fulfilled = (
        recommendation_state_before == "completed" or recommendation_state_after == "completed"
    )

    # A support decision with no approved mapping is always a real hold. Do not
    # wait until 10/10 and do not silently continue into unrelated core content.
    mapping_blocked = (
        decision.action == "support"
        and decision.recommended_item_id is None
        and attempt_id is None
        and not recommendation_fulfilled
    )
    explanation = dict(decision.explanation or {})
    if mapping_blocked:
        explanation["mapping_gap"] = "no_approved_reinforcement_selected_for_weakest_skill"
        session.status = "in_progress"
        session.completed_at = None
    elif recommendation_fulfilled:
        explanation.pop("mapping_gap", None)
        explanation["mapping_gap_resolved"] = True
        explanation["reinforcement_fulfilled"] = True
        explanation["return_to_core"] = True
    decision.explanation = explanation

    if attempt_id is not None and session.status == "completed":
        session.status = "in_progress"
        session.completed_at = None
        session.updated_at = datetime.now(timezone.utc)

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
        "session_id": session.id,
        "level_transitioned": False,
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
