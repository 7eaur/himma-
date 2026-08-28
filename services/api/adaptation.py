"""Adaptive learning policy for the Himma student journey.

Product contract (2026-08 recovery): placement happens once in the pretest. From
that starting point the ordinary learning journey moves upward only (L1 -> L2 ->
L3). A weak activity is treated inside the current level: >=80 passes, 70-79 is
a guided-retry band, and <70 requests targeted reinforcement. The historic
50/30/20 signal remains useful as a mastery trend, but it is never an early
promotion shortcut. Routine automatic demotion is intentionally disabled; a
supervisor can still make a documented manual level override.
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
    Skill,
    Student,
    User,
)
from dependencies import get_current_student, get_current_user, get_db
from runtime_flags import temporary_audio_skip_enabled

router = APIRouter(tags=["Adaptation"])
WEIGHTS = (0.50, 0.30, 0.20)  # newest -> oldest
PASS_THRESHOLD = 80.0
REINFORCEMENT_THRESHOLD = 70.0
CRITICAL_SKILL_FLOOR = 80.0
CORE_ACTIVITY_COUNT = 10

BADGE_BY_LEVEL = {
    1: "مستكشف الحروف",
    2: "بطل الكلمات",
    3: "قارئ متميز",
}

# Ordered, deterministic mappings. Supplemental canonical ids are searched
# first where they directly address the weakness; existing client-approved
# activities remain valid fallbacks. A missing target is never replaced at
# random: the supervisor-review path handles a genuine mapping gap.
REINFORCEMENT_CANONICAL_BY_SKILL_HINT: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("ربط الصوت بالحرف", ("L1-REIN-06", "L1-REIN-04")),
    ("أشكال الحرف", ("L1-REIN-07", "L1-REIN-01")),
    ("الشكل", ("L1-REIN-07", "L1-REIN-01")),
    ("الصوت الأخير", ("L1-REIN-08",)),
    ("المادة المطبوعة", ("L1-REIN-09",)),
    ("الذاكرة البصرية", ("L1-REIN-10",)),
    ("الاتجاه", ("L1-REIN-11",)),
    ("التسلسل", ("L1-REIN-12", "L3-REIN-10")),
    ("بدايات الكلمات", ("L1-REIN-02",)),
    ("الصوت الأول", ("L1-REIN-02",)),
    ("الحركات القصيرة", ("L2-REIN-06", "L2-REIN-07")),
    ("المقاطع", ("L2-REIN-02", "L2-REIN-07")),
    ("المد", ("L2-REIN-08",)),
    ("الشدة", ("L2-REIN-09",)),
    ("التنوين", ("L2-REIN-10",)),
    ("قراءة الجملة", ("L2-REIN-11", "L2-REIN-05")),
    ("دقة قراءة الكلمات", ("L3-REIN-06",)),
    ("سرعة", ("L3-REIN-07",)),
    ("طلاقة", ("L3-REIN-08", "L3-REIN-03")),
    ("المفردات", ("L3-REIN-09",)),
    ("معنى", ("L3-REIN-09",)),
    ("أحداث النص", ("L3-REIN-10",)),
)


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
    previous_low: bool = False,
    level_complete: Optional[bool] = None,
) -> tuple[str, int, str]:
    """Return the product transition without routine automatic demotion.

    ``level_complete=None`` keeps the function callable by older unit tests and
    integrations, but production evaluation always supplies an explicit value.
    ``previous_low`` is retained only for API compatibility and has no automatic
    demotion effect in the current approved journey.
    """
    del previous_low
    if mastery < REINFORCEMENT_THRESHOLD:
        return "support", current_level, "activity_below_reinforcement_threshold"
    if mastery < PASS_THRESHOLD:
        return "stay", current_level, "guided_retry_band"

    if level_complete:
        if not skill_coverage_ok:
            return "stay", current_level, "level_complete_waiting_for_skill_evidence"
        if minimum_required_skill_score is not None and minimum_required_skill_score < CRITICAL_SKILL_FLOOR:
            return "support", current_level, "level_complete_has_unresolved_weak_skill"
        if current_level < 3:
            return "promote", current_level + 1, "level_completed_next_level"
        return "stay", current_level, "top_level_completed"

    return "stay", current_level, "activity_passed_continue_level"


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
            if payload.get("declared_media_gap_skip") or payload.get("temporary_audio_skip"):
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
            # Includes temporary audio skips and unresolved audio awaiting review.
            continue
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


def _core_flow_complete(db: Session, student_id: int, level_id: int) -> bool:
    completed_ids = {
        row[0]
        for row in db.query(ContentItem.id)
        .join(Attempt, Attempt.item_id == ContentItem.id)
        .join(AssessmentSession, AssessmentSession.id == Attempt.session_id)
        .filter(
            AssessmentSession.student_id == student_id,
            AssessmentSession.assigned_level == level_id,
            Attempt.status == "completed",
            ContentItem.kind == "core_activity",
            ContentItem.level_id == level_id,
        )
        .all()
    }
    required = {
        row[0]
        for row in db.query(ContentItem.id).filter(
            ContentItem.kind == "core_activity",
            ContentItem.level_id == level_id,
        ).all()
    }
    return len(required) == CORE_ACTIVITY_COUNT and required.issubset(completed_ids)


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


def _candidate_canonical_ids(db: Session, weakest_skill_id: int) -> tuple[str, ...]:
    skill = db.query(Skill).filter(Skill.id == weakest_skill_id).first()
    if not skill:
        return ()
    haystack = " ".join(filter(None, [skill.name, skill.description, skill.canonical_skill_id])).casefold()
    candidates: list[str] = []
    for hint, canonical_ids in REINFORCEMENT_CANONICAL_BY_SKILL_HINT:
        if hint.casefold() in haystack:
            for canonical in canonical_ids:
                if canonical not in candidates:
                    candidates.append(canonical)
    return tuple(candidates)


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

    reinforcement_items = db.query(ContentItem).filter(
        ContentItem.kind == "reinforcement_activity",
        ContentItem.level_id == level_id,
    ).order_by(ContentItem.order_index, ContentItem.id).all()
    available = [item for item in reinforcement_items if item.id not in used]

    # Exact mapping remains highest priority for the original approved catalog.
    exact = next((item for item in available if item.skill_id == weakest_skill_id), None)
    if exact:
        return exact.id

    canonical_candidates = _candidate_canonical_ids(db, weakest_skill_id)
    for canonical in canonical_candidates:
        item = next(
            (candidate for candidate in available if (candidate.template_data or {}).get("canonical_id") == canonical),
            None,
        )
        if item:
            return item.id
    return None


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
        stars, reason = 3, "completed_without_help"
    elif retries:
        stars, reason = 1, "completed_after_retries"
    else:
        stars, reason = 2, "completed_with_help_without_retry"
    return stars, {"reason": reason, "retry_used": retries, "hint_used": hints}


def _add_reward_once(db: Session, reward: RewardEvent) -> bool:
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
        # A badge is a level-completion event. During temporary audio-skip testing
        # the flow may be complete with neutral voice evidence; do not fabricate
        # stars, but the completion badge is still useful for journey testing.
        if not _core_flow_complete(db, student_id, level_id):
            continue
        key = f"level:{level_id}:core-complete"
        if not db.query(RewardEvent.id).filter(
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
                    details={"event": "level_core_flow_completed", "level_id": level_id},
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
    flow_complete = _core_flow_complete(db, student.id, level_id)

    if not signals:
        return {
            "ready": False,
            "action": "hold",
            "current_level": level_id,
            "valid_attempt_count": 0,
            "required_attempt_count": 1,
            "reason": "waiting_for_valid_learning_evidence",
            "level_complete": flow_complete,
        }

    latest_signal = signals[-1]
    trend_signals = list(reversed(signals[-3:]))
    snapshot_key = ":".join(str(signal.attempt_id) for signal in trend_signals)
    existing = db.query(AdaptationDecision).filter(
        AdaptationDecision.student_id == student.id,
        AdaptationDecision.decision_source == "automatic",
        AdaptationDecision.snapshot_key == snapshot_key,
    ).first()
    if existing:
        return _decision_payload(existing)

    mastery = (
        weighted_mastery([signal.score for signal in trend_signals])
        if len(trend_signals) == 3
        else latest_signal.score
    )
    coverage_ok, minimum_skill_score, weakest_skill_id = _skill_gate_state(db, level_id, signals)

    # Temporary voice skips are deliberately neutral. They may remove a skill
    # from coverage while the tester still needs to traverse the whole product.
    # Only that test mode may relax missing evidence; known scored weaknesses
    # remain blocking and are still reinforced.
    provisional_testing = bool(temporary_audio_skip_enabled() and flow_complete)
    effective_coverage = coverage_ok or provisional_testing
    effective_minimum = minimum_skill_score

    if latest_signal.score < REINFORCEMENT_THRESHOLD:
        action, new_level, reason = "support", level_id, "activity_below_reinforcement_threshold"
        weakest_skill_id = latest_signal.skill_id
    elif flow_complete:
        action, new_level, reason = decide_transition(
            current_level=level_id,
            mastery=max(PASS_THRESHOLD, latest_signal.score),
            skill_coverage_ok=effective_coverage,
            minimum_required_skill_score=effective_minimum,
            level_complete=True,
        )
    else:
        action, new_level, reason = decide_transition(
            current_level=level_id,
            mastery=latest_signal.score,
            skill_coverage_ok=coverage_ok,
            minimum_required_skill_score=minimum_skill_score,
            level_complete=False,
        )

    # Do not let a historical low score force reinforcement after a later
    # successful activity. Weakness intervention is attached to the current
    # activity snapshot only.
    recommended_item_id = None
    if action == "support":
        recommended_item_id = _recommended_reinforcement(db, student.id, level_id, weakest_skill_id)

    explanation = {
        "policy_version": "UPWARD_JOURNEY_V2",
        "weights_newest_to_oldest": list(WEIGHTS),
        "attempts_newest_to_oldest": [
            {"attempt_id": signal.attempt_id, "skill_id": signal.skill_id, "score": signal.score}
            for signal in trend_signals
        ],
        "latest_activity_score": latest_signal.score,
        "level_complete": flow_complete,
        "skill_coverage_ok": coverage_ok,
        "minimum_required_skill_score": minimum_skill_score,
        "required_skill_floor": CRITICAL_SKILL_FLOOR,
        "pass_threshold": PASS_THRESHOLD,
        "guided_retry_threshold": REINFORCEMENT_THRESHOLD,
        "routine_automatic_demotion": False,
        "temporary_audio_test_provisional": provisional_testing,
        "reinforcement_assignment": "deterministic_skill_mapping" if recommended_item_id else None,
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
        consecutive_low_count=1 if latest_signal.score < REINFORCEMENT_THRESHOLD else 0,
        snapshot_key=snapshot_key,
        explanation=explanation,
    )
    db.add(decision)
    # Level mutation is deliberately performed by adaptation_runtime only after
    # it has closed the old level session and created the next level session.
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
        explanation={"reason": "supervisor_manual_override"},
        manual_reason=body.reason.strip(),
        actor_id=user.id,
    )
    student.current_level = body.new_level
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return _decision_payload(decision)
