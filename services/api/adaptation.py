"""P06 adaptive learning engine and event-backed rewards.

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
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.adaptation_models import AdaptationDecision, RewardEvent
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

BADGE_BY_LEVEL = {
    1: "مستكشف الحروف",
    2: "بطل الكلمات",
    3: "قارئ متميز",
}


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
    # The approved source does not mark a smaller critical-skill subset in the
    # executable catalog. Conservatively, every core skill is treated as required;
    # this prevents a false promotion and can be relaxed only by an explicit map.
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


def _recommended_reinforcement(db: Session, student_id: int, level_id: int, weakest_skill_id: Optional[int]) -> Optional[int]:
    if weakest_skill_id is None:
        return None
    used = {
        row[0]
        for row in db.query(Attempt.item_id)
        .join(AssessmentSession, AssessmentSession.id == Attempt.session_id)
        .join(ContentItem, ContentItem.id == Attempt.item_id)
        .filter(
            AssessmentSession.student_id == student_id,
            ContentItem.kind == "reinforcement_activity",
            ContentItem.level_id == level_id,
        )
        .all()
    }
    query = db.query(ContentItem).filter(
        ContentItem.kind == "reinforcement_activity",
        ContentItem.level_id == level_id,
        ContentItem.skill_id == weakest_skill_id,
    )
    if used:
        query = query.filter(ContentItem.id.notin_(used))
    item = query.order_by(ContentItem.order_index).first()
    return item.id if item else None


def _stars_for_attempt(db: Session, attempt: Attempt) -> tuple[int, dict]:
    structured = db.query(ActivityStepResponse).filter(
        ActivityStepResponse.attempt_id == attempt.id,
    ).order_by(ActivityStepResponse.step_id, ActivityStepResponse.attempt_no).all()
    hints = any(row.hint_used for row in structured)
    by_step: dict[int, list[ActivityStepResponse]] = {}
    for row in structured:
        by_step.setdefault(row.step_id, []).append(row)
    retries = any(len(rows) > 1 for rows in by_step.values())

    if not retries and not hints:
        stars = 3
        reason = "completed_without_help"
    elif retries:
        stars = 1
        reason = "completed_after_retries"
    else:
        # The client source line for the two-star wording is incomplete. This
        # middle bucket is intentionally limited to a completed activity that
        # used help but did not require a repeated submitted attempt.
        stars = 2
        reason = "completed_with_help_without_retry"
    return stars, {"reason": reason, "retry_used": retries, "hint_used": hints}


def _add_reward_once(db: Session, reward: RewardEvent) -> bool:
    """Insert a reward without allowing a concurrent duplicate to abort the outer transaction.

    Reward generation is called by several student endpoints (status, next activity,
    rewards) and those requests can overlap in a browser. The database unique key is
    the final authority; a savepoint contains the expected loser of that race.
    """
    try:
        with db.begin_nested():
            db.add(reward)
            db.flush()
        return True
    except IntegrityError:
        return False


def ensure_rewards(db: Session, student_id: int) -> list[RewardEvent]:
    completed = (
        db.query(Attempt, ContentItem, AssessmentSession)
        .join(ContentItem, ContentItem.id == Attempt.item_id)
        .join(AssessmentSession, AssessmentSession.id == Attempt.session_id)
        .filter(
            AssessmentSession.student_id == student_id,
            Attempt.status == "completed",
            ContentItem.kind.in_(["core_activity", "reinforcement_activity"]),
        )
        .order_by(Attempt.id)
        .all()
    )
    changed = False
    for attempt, item, session in completed:
        # Rewards must represent a real, academically valid completion. A
        # gap-only round, unresolved/low-confidence recording, rerecord request,
        # or otherwise incomplete evidence is neutral and earns no stars yet.
        if _attempt_signal(db, attempt, item) is None:
            continue
        key = f"activity:{attempt.id}:stars"
        exists = db.query(RewardEvent.id).filter(
            RewardEvent.student_id == student_id,
            RewardEvent.reward_key == key,
        ).first()
        if not exists:
            stars, details = _stars_for_attempt(db, attempt)
            changed = _add_reward_once(
                db,
                RewardEvent(
                    student_id=student_id,
                    attempt_id=attempt.id,
                    reward_type="stars",
                    reward_key=key,
                    stars=stars,
                    label=f"{stars} من 3",
                    details={**details, "item_id": item.id, "level_id": item.level_id},
                ),
            ) or changed

    for level_id, label in BADGE_BY_LEVEL.items():
        completed_core = (
            db.query(Attempt, ContentItem)
            .join(ContentItem, ContentItem.id == Attempt.item_id)
            .join(AssessmentSession, AssessmentSession.id == Attempt.session_id)
            .filter(
                AssessmentSession.student_id == student_id,
                Attempt.status == "completed",
                ContentItem.kind == "core_activity",
                ContentItem.level_id == level_id,
            )
            .all()
        )
        valid_completed_core = sum(
            1 for attempt, item in completed_core if _attempt_signal(db, attempt, item) is not None
        )
        key = f"level:{level_id}:core-complete"
        if valid_completed_core >= 10 and not db.query(RewardEvent.id).filter(
            RewardEvent.student_id == student_id,
            RewardEvent.reward_key == key,
        ).first():
            changed = _add_reward_once(
                db,
                RewardEvent(
                    student_id=student_id,
                    attempt_id=None,
                    reward_type="badge",
                    reward_key=key,
                    stars=None,
                    label=label,
                    details={"event": "ten_valid_core_activities_completed", "level_id": level_id},
                ),
            ) or changed

    if changed:
        db.commit()
    return db.query(RewardEvent).filter(
        RewardEvent.student_id == student_id,
    ).order_by(RewardEvent.id).all()


def evaluate_student(db: Session, student: Student) -> dict:
    ensure_rewards(db, student.id)
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
    recommended_item_id = None
    if action in {"support", "stay"} and reason != "top_level_mastery":
        recommended_item_id = _recommended_reinforcement(db, student.id, level_id, weakest_skill_id)
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
        "reinforcement_assignment": "exact_weakest_skill_match" if recommended_item_id else None,
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
        recommended_item_id=recommended_item_id,
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
        "recommended_item_id": decision.recommended_item_id,
        "valid_attempt_count": decision.valid_attempt_count,
        "consecutive_low_count": decision.consecutive_low_count,
        "explanation": decision.explanation,
        "manual_reason": decision.manual_reason,
        "created_at": decision.created_at,
    }


def _reward_payload(reward: RewardEvent) -> dict:
    return {
        "id": reward.id,
        "type": reward.reward_type,
        "key": reward.reward_key,
        "stars": reward.stars,
        "label": reward.label,
        "details": reward.details,
        "created_at": reward.created_at,
    }


@router.get("/adaptation/status")
def adaptation_status(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    return evaluate_student(db, student)


@router.get("/rewards")
def student_rewards(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    return [_reward_payload(row) for row in ensure_rewards(db, student.id)]


@router.get("/researcher/students/{student_id}/adaptation/history")
def researcher_adaptation_history(
    student_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")
    return [
        _decision_payload(row)
        for row in db.query(AdaptationDecision)
        .filter(AdaptationDecision.student_id == student_id)
        .order_by(AdaptationDecision.id)
        .all()
    ]


@router.get("/researcher/students/{student_id}/rewards")
def researcher_rewards(
    student_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")
    return [_reward_payload(row) for row in ensure_rewards(db, student_id)]


@router.post("/researcher/students/{student_id}/adaptation/manual-override")
def manual_override(
    student_id: int,
    body: ManualOverrideRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(Student.id == student_id).with_for_update().first()
    if not student:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")
    previous_level = student.current_level
    decision = AdaptationDecision(
        student_id=student.id,
        decision_source="manual",
        action="override",
        mastery_score=None,
        previous_level=previous_level,
        new_level=body.new_level,
        weakest_skill_id=None,
        recommended_item_id=None,
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
