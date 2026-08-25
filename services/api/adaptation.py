"""P06 adaptive learning engine.

Academic rules come from the approved Himma requirements: the newest three valid
attempts are weighted 50/30/20; <50 receives support first and can demote only
on a second consecutive low decision; >=80 may promote only with skill coverage
and no required skill below 60. Invalid/incomplete/unresolved audio attempts are
excluded rather than penalised.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.adaptation_models import AdaptationDecision
from db.activity_models import ActivityStepResponse
from db.models import (
    AssessmentSession,
    Attempt,
    AttemptResponse,
    AudioSubmission,
    ContentItem,
    ContentStep,
    Student,
    User,
)
from dependencies import get_current_student, get_current_user, get_db

router = APIRouter(tags=["Adaptation"])
WEIGHTS = (0.50, 0.30, 0.20)  # newest -> oldest
PROMOTION_THRESHOLD = 80.0
SUPPORT_THRESHOLD = 50.0
CRITICAL_SKILL_FLOOR = 60.0


@dataclass(frozen=True)
class AttemptSignal:
    attempt_id: int
    skill_id: int
    score: float


class ManualOverrideRequest(BaseModel):
    new_level: int = Field(ge=1, le=3)
    reason: str = Field(min_length=5, max_length=1000)


def weighted_mastery(newest_first_scores: list[float]) -> float:
    if len(newest_first_scores) != 3:
        raise ValueError("Exactly three valid scores are required")
    return round(sum(score * weight for score, weight in zip(newest_first_scores, WEIGHTS)), 4)


def decide_transition(
    *,
    current_level: int,
    mastery: float,
    skill_coverage_ok: bool,
    minimum_required_skill_score: Optional[float],
    previous_low: bool,
) -> tuple[str, int, str]:
    if mastery < SUPPORT_THRESHOLD:
        if previous_low and current_level > 1:
            return "demote", current_level - 1, "second_consecutive_low_mastery"
        return "support", current_level, "low_mastery_support_first"

    if mastery >= PROMOTION_THRESHOLD:
        if current_level >= 3:
            return "stay", current_level, "top_level_mastery"
        if not skill_coverage_ok:
            return "stay", current_level, "promotion_waiting_for_skill_coverage"
        if minimum_required_skill_score is None or minimum_required_skill_score < CRITICAL_SKILL_FLOOR:
            return "stay", current_level, "promotion_blocked_by_skill_floor"
        return "promote", current_level + 1, "mastery_and_skill_gates_passed"

    return "stay", current_level, "mastery_in_stability_band"


def _attempt_signal(db: Session, attempt: Attempt, item: ContentItem) -> Optional[AttemptSignal]:
    if attempt.status != "completed":
        return None

    scores: list[bool] = []
    for step in db.query(ContentStep).filter(ContentStep.item_id == item.id).order_by(ContentStep.order_index).all():
        structured = (
            db.query(ActivityStepResponse)
            .filter(
                ActivityStepResponse.attempt_id == attempt.id,
                ActivityStepResponse.step_id == step.id,
            )
            .order_by(ActivityStepResponse.attempt_no.desc())
            .first()
        )
        if structured:
            payload = structured.response_payload or {}
            if payload.get("declared_media_gap_skip"):
                # A declared missing source asset is academically neutral.
                continue
            scores.append(bool(structured.is_correct))
            continue

        response = db.query(AttemptResponse).filter(
            AttemptResponse.attempt_id == attempt.id,
            AttemptResponse.step_id == step.id,
        ).first()
        if not response:
            return None
        audio = db.query(AudioSubmission).filter(AudioSubmission.response_id == response.id).first()
        if audio and audio.status == "rerecord_required":
            return None
        if response.is_correct is None:
            # Includes unresolved / low-confidence audio pending human review.
            return None
        scores.append(bool(response.is_correct))

    if not scores:
        return None
    return AttemptSignal(
        attempt_id=attempt.id,
        skill_id=item.skill_id,
        score=round((sum(1 for value in scores if value) / len(scores)) * 100.0, 4),
    )


def _valid_signals(db: Session, student_id: int, level_id: int) -> list[AttemptSignal]:
    rows = (
        db.query(Attempt, ContentItem)
        .join(AssessmentSession, AssessmentSession.id == Attempt.session_id)
        .join(ContentItem, ContentItem.id == Attempt.item_id)
        .filter(
            AssessmentSession.student_id == student_id,
            AssessmentSession.assigned_level == level_id,
            Attempt.status == "completed",
            ContentItem.level_id == level_id,
            ContentItem.kind.in_(["core_activity", "reinforcement_activity"]),
        )
        .order_by(Attempt.completed_at, Attempt.id)
        .all()
    )
    signals: list[AttemptSignal] = []
    for attempt, item in rows:
        signal = _attempt_signal(db, attempt, item)
        if signal is not None:
            signals.append(signal)
    return signals


def _skill_gate_state(db: Session, level_id: int, signals: list[AttemptSignal]) -> tuple[bool, Optional[float], Optional[int]]:
    required_skill_ids = {
        row[0]
        for row in db.query(ContentItem.skill_id)
        .filter(ContentItem.kind == "core_activity", ContentItem.level_id == level_id)
        .distinct()
        .all()
    }
    latest_by_skill: dict[int, float] = {}
    for signal in signals:
        latest_by_skill[signal.skill_id] = signal.score
    coverage_ok = bool(required_skill_ids) and required_skill_ids.issubset(latest_by_skill)
    if not latest_by_skill:
        return coverage_ok, None, None
    weakest_skill_id = min(latest_by_skill, key=latest_by_skill.get)
    required_scores = [latest_by_skill[skill_id] for skill_id in required_skill_ids if skill_id in latest_by_skill]
    minimum = min(required_scores) if required_scores else None
    return coverage_ok, minimum, weakest_skill_id


def evaluate_student(db: Session, student: Student) -> dict:
    level_id = student.current_level
    signals = _valid_signals(db, student.id, level_id)
    if len(signals) < 3:
        return {
            "ready": False,
            "action": "hold",
            "current_level": level_id,
            "valid_attempt_count": len(signals),
            "required_attempt_count": 3,
            "reason": "waiting_for_three_valid_attempts",
        }

    latest = list(reversed(signals[-3:]))
    snapshot_key = ":".join(str(signal.attempt_id) for signal in latest)
    existing = db.query(AdaptationDecision).filter(
        AdaptationDecision.student_id == student.id,
        AdaptationDecision.decision_source == "automatic",
        AdaptationDecision.snapshot_key == snapshot_key,
    ).first()
    if existing:
        return _decision_payload(existing)

    mastery = weighted_mastery([signal.score for signal in latest])
    coverage_ok, minimum_skill_score, weakest_skill_id = _skill_gate_state(db, level_id, signals)
    previous = (
        db.query(AdaptationDecision)
        .filter(
            AdaptationDecision.student_id == student.id,
            AdaptationDecision.decision_source == "automatic",
        )
        .order_by(AdaptationDecision.id.desc())
        .first()
    )
    previous_low = bool(previous and previous.mastery_score is not None and float(previous.mastery_score) < SUPPORT_THRESHOLD)
    action, new_level, reason = decide_transition(
        current_level=level_id,
        mastery=mastery,
        skill_coverage_ok=coverage_ok,
        minimum_required_skill_score=minimum_skill_score,
        previous_low=previous_low,
    )
    low_count = (int(previous.consecutive_low_count) + 1 if previous_low else 1) if mastery < SUPPORT_THRESHOLD else 0
    explanation = {
        "weights_newest_to_oldest": list(WEIGHTS),
        "attempts_newest_to_oldest": [
            {"attempt_id": signal.attempt_id, "skill_id": signal.skill_id, "score": signal.score}
            for signal in latest
        ],
        "skill_coverage_ok": coverage_ok,
        "minimum_required_skill_score": minimum_skill_score,
        "required_skill_floor": CRITICAL_SKILL_FLOOR,
        "promotion_threshold": PROMOTION_THRESHOLD,
        "support_threshold": SUPPORT_THRESHOLD,
        "reason": reason,
    }
    decision = AdaptationDecision(
        student_id=student.id,
        decision_source="automatic",
        action=action,
        mastery_score=Decimal(str(mastery)),
        previous_level=level_id,
        new_level=new_level,
        weakest_skill_id=weakest_skill_id,
        valid_attempt_count=len(signals),
        consecutive_low_count=low_count,
        snapshot_key=snapshot_key,
        explanation=explanation,
    )
    db.add(decision)
    if new_level != level_id:
        student.current_level = new_level
    db.commit()
    db.refresh(decision)
    return _decision_payload(decision)


def _decision_payload(decision: AdaptationDecision) -> dict:
    return {
        "ready": True,
        "decision_id": decision.id,
        "source": decision.decision_source,
        "action": decision.action,
        "mastery_score": float(decision.mastery_score) if decision.mastery_score is not None else None,
        "previous_level": decision.previous_level,
        "new_level": decision.new_level,
        "weakest_skill_id": decision.weakest_skill_id,
        "valid_attempt_count": decision.valid_attempt_count,
        "consecutive_low_count": decision.consecutive_low_count,
        "explanation": decision.explanation,
        "manual_reason": decision.manual_reason,
        "created_at": decision.created_at,
    }


@router.get("/adaptation/status")
def adaptation_status(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    return evaluate_student(db, student)


@router.get("/researcher/students/{student_id}/adaptation/history")
def adaptation_history(
    student_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    rows = db.query(AdaptationDecision).filter(
        AdaptationDecision.student_id == student_id,
    ).order_by(AdaptationDecision.id).all()
    return [_decision_payload(row) for row in rows]


@router.post("/researcher/students/{student_id}/adaptation/manual-override")
def manual_override(
    student_id: int,
    body: ManualOverrideRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(Student.id == student_id).with_for_update().first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    previous_level = student.current_level
    decision = AdaptationDecision(
        student_id=student.id,
        decision_source="manual",
        action="override",
        mastery_score=None,
        previous_level=previous_level,
        new_level=body.new_level,
        weakest_skill_id=None,
        valid_attempt_count=0,
        consecutive_low_count=0,
        snapshot_key=None,
        explanation={"reason": "researcher_manual_override"},
        manual_reason=body.reason.strip(),
        actor_id=user.id,
    )
    student.current_level = body.new_level
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return _decision_payload(decision)
