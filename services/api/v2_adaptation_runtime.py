"""P05 command/query service for V2 evidence, support and progression."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.learning_models import (
    AdaptationDecision,
    LessonQuestionResponse,
    LessonSession,
    SkillEvidence,
    StudentJourney,
    SupportAssignment,
)
from db.models import Student, User
from dependencies import get_current_user, get_db
from v2_adaptation_policy import (
    POLICY_VERSION,
    EvidenceSignal,
    PolicyDecision,
    evaluate_independent,
    evaluate_support,
    resolve_focus,
)
from v2_content.repository import get_question, get_release, get_support
from v2_lesson_runtime import _require_preview_student, _session_or_404


router = APIRouter(prefix="/v2/adaptation", tags=["v2-adaptation"])


def active_support_assignment(db: Session, session_id: int) -> SupportAssignment | None:
    return db.query(SupportAssignment).filter(
        SupportAssignment.lesson_session_id == session_id,
        SupportAssignment.status.in_(("active", "waiting_review")),
    ).order_by(SupportAssignment.id.desc()).first()


def record_response_evidence(
    db: Session,
    session: LessonSession,
    response: LessonQuestionResponse,
    question: dict[str, Any],
    assignment: SupportAssignment | None,
) -> SkillEvidence:
    existing = db.query(SkillEvidence).filter(SkillEvidence.response_id == response.id).one_or_none()
    if existing:
        return existing
    resolved = resolve_focus(question)
    evidence = SkillEvidence(
        response_id=response.id,
        lesson_session_id=session.id,
        student_id=session.student_id,
        content_release_id=session.content_release_id,
        support_assignment_id=assignment.id if assignment else None,
        question_id=question["id"],
        source_kind="support" if assignment else "lesson",
        role=question["role"],
        skill_group=question["skill_group"],
        evidence_type=question["evidence_type"],
        error_focus=question.get("error_focus"),
        support_focus=assignment.focus if assignment else (resolved[1] if resolved else None),
        review_status=response.status,
        is_correct=response.is_correct,
        hint_used=response.hint_used,
        counts_for_mastery=question["role"] in {"independent_check", "support_check"}
        and response.status == "graded",
        policy_version=POLICY_VERSION,
        reviewed_at=response.reviewed_at,
    )
    db.add(evidence)
    db.flush()
    return evidence


def _signals(rows: list[SkillEvidence], lesson_id: str) -> list[EvidenceSignal]:
    return [
        EvidenceSignal(
            evidence_id=row.id,
            question_id=row.question_id,
            lesson_id=lesson_id,
            skill_group=row.skill_group,
            evidence_type=row.evidence_type,
            error_focus=row.error_focus,
            is_correct=row.is_correct,
            review_status=row.review_status,
        )
        for row in rows
    ]


def _decision(
    db: Session,
    session: LessonSession,
    decision_key: str,
    outcome: PolicyDecision,
    assignment: SupportAssignment | None = None,
) -> AdaptationDecision:
    existing = db.query(AdaptationDecision).filter(
        AdaptationDecision.lesson_session_id == session.id,
        AdaptationDecision.decision_key == decision_key,
    ).one_or_none()
    if existing:
        return existing
    row = AdaptationDecision(
        lesson_session_id=session.id,
        student_id=session.student_id,
        content_release_id=session.content_release_id,
        support_assignment_id=assignment.id if assignment else None,
        decision_key=decision_key,
        decision_kind=outcome.kind,
        reason_code=outcome.reason_code,
        evidence_ids=list(outcome.evidence_ids),
        explanation_json={
            "support_id": outcome.support_id,
            "focus": outcome.focus,
            "source_lesson_id": session.lesson_id,
            "no_automatic_demotion": True,
        },
        policy_version=POLICY_VERSION,
    )
    db.add(row)
    db.flush()
    return row


def _support_level(support: dict[str, Any]) -> int:
    levels = [int(value[1]) for value in support.get("linked_lessons", []) if len(value) >= 2 and value[1].isdigit()]
    return min(levels) if levels else 1


def _open_support(
    db: Session,
    session: LessonSession,
    outcome: PolicyDecision,
) -> SupportAssignment:
    if not outcome.support_id or not outcome.focus:
        raise RuntimeError("support outcome is missing its approved focus")
    support = get_support(outcome.support_id)
    if not support:
        raise RuntimeError("support definition is missing from the pinned release")
    focus_map = (support.get("focus_item_map") or {}).get(outcome.focus)
    if not focus_map or len(focus_map.get("check_ids") or []) != 2:
        raise RuntimeError("support focus does not provide exactly two checks")
    mode = "additional_check" if outcome.kind == "additional_check" else "targeted_support"
    assignment = SupportAssignment(
        lesson_session_id=session.id,
        student_id=session.student_id,
        content_release_id=session.content_release_id,
        support_id=support["id"],
        focus=outcome.focus,
        target_skill=support["target_skill"],
        source_lesson_id=session.lesson_id,
        source_level=int(session.lesson_id[1]),
        support_level=_support_level(support),
        mode=mode,
        practice_question_ids=list(focus_map.get("practice_ids") or []),
        check_question_ids=list(focus_map["check_ids"]),
        return_to={
            "lesson_id": session.lesson_id,
            "stage": "complete",
            "path": f"/student/learning-v2/{session.id}",
        },
        policy_version=POLICY_VERSION,
    )
    db.add(assignment)
    db.flush()
    session.stage = "additional_check" if mode == "additional_check" else "support_practice"
    session.step_index = 0
    session.status = "in_progress"
    session.version += 1
    session.updated_at = datetime.now(timezone.utc)
    return assignment


def _complete_lesson(db: Session, session: LessonSession, assignment: SupportAssignment | None = None) -> None:
    now = datetime.now(timezone.utc)
    if assignment:
        assignment.status = "resolved"
        assignment.resolved_at = now
        assignment.updated_at = now
    session.stage = "complete"
    session.status = "completed"
    session.step_index = 0
    session.completed_at = now
    session.updated_at = now
    session.version += 1

    journey = db.query(StudentJourney).filter(StudentJourney.student_id == session.student_id).with_for_update().one_or_none()
    if not journey:
        return
    lessons = get_release()["lessons"]
    ids = [row["id"] for row in lessons]
    index = ids.index(session.lesson_id)
    if index + 1 < len(lessons):
        next_lesson = lessons[index + 1]
        journey.current_lesson_id = next_lesson["id"]
        journey.current_level = int(next_lesson["level"][1])
    else:
        journey.current_lesson_id = None
        journey.current_level = 3
        journey.placement_state = "posttest_ready"
    journey.version += 1
    journey.updated_at = now
    from v2_rewards import reconcile_rewards
    reconcile_rewards(db, session.student_id, lesson_session_id=session.id)


def finish_independent_check(db: Session, session: LessonSession, *, decision_key: str = "independent:1") -> AdaptationDecision:
    rows = db.query(SkillEvidence).filter(
        SkillEvidence.lesson_session_id == session.id,
        SkillEvidence.support_assignment_id.is_(None),
        SkillEvidence.role == "independent_check",
    ).order_by(SkillEvidence.id).all()
    questions = {row.question_id: get_question(row.question_id) for row in rows}
    if any(value is None for value in questions.values()):
        raise RuntimeError("independent evidence references missing release questions")
    outcome = evaluate_independent(_signals(rows, session.lesson_id), questions)  # type: ignore[arg-type]
    decision = _decision(db, session, decision_key, outcome)
    if outcome.kind == "next_lesson":
        _complete_lesson(db, session)
    elif outcome.kind in {"additional_check", "targeted_support"}:
        assignment = _open_support(db, session, outcome)
        decision.support_assignment_id = assignment.id
    elif outcome.kind == "waiting_review":
        session.stage = "waiting_review"
        session.status = "waiting_review"
        session.step_index = 0
        session.version += 1
    else:
        session.stage = "supervisor_hold"
        session.status = "waiting_review"
        session.step_index = 0
        session.version += 1
    return decision


def finish_support_check(db: Session, session: LessonSession, assignment: SupportAssignment, *, decision_key: str | None = None) -> AdaptationDecision:
    rows = db.query(SkillEvidence).filter(
        SkillEvidence.lesson_session_id == session.id,
        SkillEvidence.support_assignment_id == assignment.id,
        SkillEvidence.role == "support_check",
    ).order_by(SkillEvidence.id).all()
    was_additional = assignment.mode == "additional_check"
    outcome = evaluate_support(_signals(rows, session.lesson_id), was_additional_check=was_additional)
    decision = _decision(db, session, decision_key or f"support:{assignment.id}:1", outcome, assignment)
    now = datetime.now(timezone.utc)
    if outcome.kind == "next_lesson":
        _complete_lesson(db, session, assignment)
    elif outcome.kind == "targeted_support" and was_additional:
        assignment.mode = "targeted_support"
        assignment.verification_round = 1
        assignment.updated_at = now
        session.stage = "support_practice"
        session.step_index = 0
        session.version += 1
        session.updated_at = now
    elif outcome.kind == "waiting_review":
        assignment.status = "waiting_review"
        assignment.updated_at = now
        session.stage = "waiting_review"
        session.status = "waiting_review"
        session.step_index = 0
        session.version += 1
    else:
        assignment.status = "escalated"
        assignment.updated_at = now
        session.stage = "supervisor_hold"
        session.status = "waiting_review"
        session.step_index = 0
        session.version += 1
    return decision


def student_adaptation_payload(db: Session, session: LessonSession) -> dict[str, Any] | None:
    latest = db.query(AdaptationDecision).filter(
        AdaptationDecision.lesson_session_id == session.id,
    ).order_by(AdaptationDecision.id.desc()).first()
    assignment = active_support_assignment(db, session.id)
    if not latest and not assignment:
        return None
    messages = {
        "additional_check": "سنجرّب سؤالين قصيرين لنتأكد مما تحتاجه.",
        "targeted_support": "لديك مساعدة قصيرة ثم تعود إلى مسارك.",
        "waiting_review": "إجابتك محفوظة وتنتظر مراجعة المشرف.",
        "supervisor_hold": "سيختار المشرف أفضل خطوة مساعدة لك.",
        "next_lesson": "أحسنت، أصبحت خطوتك التالية جاهزة.",
    }
    kind = latest.decision_kind if latest else assignment.mode
    return {
        "state": kind,
        "message": messages.get(kind, "تقدمك محفوظ بأمان."),
        "support": {
            "support_id": assignment.support_id,
            "title": get_support(assignment.support_id)["title"],
            "focus": assignment.focus,
            "mode": assignment.mode,
        } if assignment else None,
        "policy_version": POLICY_VERSION,
    }


@router.get("/sessions/{session_id}/status")
def adaptation_status(
    session_id: int,
    student: Student = Depends(_require_preview_student),
    db: Session = Depends(get_db),
):
    """Read-only learner query; decisions are created only by answer commands."""
    session = _session_or_404(db, session_id, student.id)
    return {"session_id": session.id, "adaptation": student_adaptation_payload(db, session)}


@router.get("/admin/sessions/{session_id}/decision")
def adaptation_decision_for_supervisor(
    session_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(LessonSession).filter(LessonSession.id == session_id).one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="جلسة الدرس غير موجودة")
    decisions = db.query(AdaptationDecision).filter(
        AdaptationDecision.lesson_session_id == session.id,
    ).order_by(AdaptationDecision.id).all()
    return {
        "session_id": session.id,
        "student_id": session.student_id,
        "lesson_id": session.lesson_id,
        "decisions": [
            {
                "decision_kind": row.decision_kind,
                "reason_code": row.reason_code,
                "evidence_ids": row.evidence_ids,
                "explanation": row.explanation_json,
                "policy_version": row.policy_version,
                "created_at": row.created_at.isoformat(),
            }
            for row in decisions
        ],
    }
