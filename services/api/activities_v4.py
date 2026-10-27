"""Core-session compatibility and critical-skill selection helpers.

This module is deliberately *not* an HTTP router. ``activity_runtime.py`` owns
all mounted ``/activities`` endpoints. The helpers kept here are the small,
proven pieces still required by that canonical runtime while the historical V4
route generation is retired.
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from activities import _activity_session_or_404
from adaptation import _load_policy, _valid_signals
from db.models import AssessmentSession, Skill


def _active_core_session(db: Session, student_id: int) -> AssessmentSession | None:
    """Return the newest active Core session for one student, if any."""
    return (
        db.query(AssessmentSession)
        .filter(
            AssessmentSession.student_id == student_id,
            AssessmentSession.session_type == "core",
            AssessmentSession.status == "in_progress",
        )
        .order_by(AssessmentSession.id.desc())
        .first()
    )


def _resolve_active_session(
    db: Session,
    *,
    requested_session_id: int,
    student_id: int,
) -> AssessmentSession:
    """Bridge a historical route id to the student's current Core session.

    An already-open browser route remains usable across an early promotion
    without mutating or relabelling the completed historical session.
    """
    requested = _activity_session_or_404(
        db,
        requested_session_id,
        student_id,
        require_active=False,
    )
    if requested.status == "in_progress":
        return requested
    active = _active_core_session(db, student_id)
    if active is None:
        raise HTTPException(status_code=404, detail="جلسة التعلم غير موجودة أو انتهت")
    return active


def _preferred_core_skill_id(
    db: Session,
    *,
    student_id: int,
    session_id: int,
    level_id: int,
) -> int | None:
    """Choose a configured critical skill needing evidence in this session."""
    policy = _load_policy()
    codes = [
        str(code)
        for code in policy.get("critical_skill_codes_by_level", {}).get(str(level_id), [])
        if str(code).strip()
    ]
    if not codes:
        return None

    skills = db.query(Skill).filter(
        Skill.level_id == level_id,
        Skill.canonical_skill_id.in_(codes),
    ).all()
    by_code = {skill.canonical_skill_id: skill for skill in skills}
    if any(code not in by_code for code in codes):
        return None

    latest_by_skill: dict[int, float] = {}
    for signal in _valid_signals(db, student_id, level_id, session_id=session_id):
        latest_by_skill[signal.skill_id] = signal.score

    for code in codes:
        skill_id = by_code[code].id
        if skill_id not in latest_by_skill:
            return skill_id

    return min(
        (by_code[code].id for code in codes),
        key=lambda skill_id: (latest_by_skill[skill_id], skill_id),
    )
