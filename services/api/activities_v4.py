"""V4 activity routing bridge.

This router is registered ahead of the legacy activity router and owns the
`GET /activities/session/{id}/next` route. All other activity endpoints remain
on the proven Stage-2 implementation.

Why this bridge exists:
- early promotion can close the current level session while `/next` is running;
  the old runner would then accidentally prepare another item in that closed
  session, making the following submit return 404;
- normal Core selection should prefer missing/weak critical-skill evidence,
  using order_index only as a deterministic tie-breaker.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from activities import (
    _activity_session_or_404,
    _finalize_attempt_if_done,
    _finalize_session_if_done,
    _load_item,
    _pending_attempt,
    _rich_item_query,
    _step_payload,
    _step_state,
    router as legacy_activities_router,
)
from adaptation import _load_policy, _valid_signals
from adaptation_runtime import prepare_next_for_student
from db.models import AssessmentSession, Attempt, ContentItem, Skill, Student
from dependencies import get_current_student, get_db

router = APIRouter()


def _preferred_core_skill_id(db: Session, *, student_id: int, level_id: int) -> int | None:
    """Choose a critical skill needing evidence, deterministically.

    Missing configured critical-skill evidence is prioritized first. Once every
    configured critical skill has evidence, the weakest latest critical skill is
    preferred. If the policy is missing/mismatched, return None and let the
    approved order-index fallback operate rather than inventing a skill rule.
    """
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
    for signal in _valid_signals(db, student_id, level_id):
        latest_by_skill[signal.skill_id] = signal.score

    for code in codes:
        skill_id = by_code[code].id
        if skill_id not in latest_by_skill:
            return skill_id

    return min(
        (by_code[code].id for code in codes),
        key=lambda skill_id: (latest_by_skill[skill_id], skill_id),
    )


def _next_unused_core_item(
    db: Session,
    *,
    student_id: int,
    session_id: int,
    level_id: int,
) -> ContentItem | None:
    completed_ids = {
        row[0]
        for row in db.query(Attempt.item_id).filter(
            Attempt.session_id == session_id,
            Attempt.status == "completed",
        ).all()
    }
    base = _rich_item_query(db).filter(
        ContentItem.kind == "core_activity",
        ContentItem.level_id == level_id,
        ContentItem.status == "approved",
    )
    if completed_ids:
        base = base.filter(ContentItem.id.notin_(completed_ids))

    target_skill_id = _preferred_core_skill_id(db, student_id=student_id, level_id=level_id)
    if target_skill_id is not None:
        preferred = base.filter(ContentItem.skill_id == target_skill_id).order_by(
            ContentItem.order_index,
            ContentItem.id,
        ).first()
        if preferred is not None:
            return preferred

    return base.order_by(ContentItem.order_index, ContentItem.id).first()


@router.get("/activities/session/{session_id}/next")
def next_activity_step_v4(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = _activity_session_or_404(db, session_id, student.id)

    pending_attempt = _pending_attempt(db, session.id)
    if pending_attempt:
        item = _load_item(db, pending_attempt.item_id)
        if not item:
            raise HTTPException(status_code=409, detail="تعذر تحميل محتوى النشاط")
        for step in item.steps:
            if not _step_state(db, pending_attempt, step)["done"]:
                return _step_payload(db, item, pending_attempt, step)
        _finalize_attempt_if_done(db, pending_attempt, item)
        db.commit()

    prepared = prepare_next_for_student(db, student, session)
    if prepared.get("mapping_blocked"):
        raise HTTPException(
            status_code=409,
            detail="يحتاج المسار إلى ربط نشاط تقوية معتمد للمهارة الأضعف قبل المتابعة.",
        )
    if prepared.get("verification_escalated"):
        raise HTTPException(
            status_code=409,
            detail="يحتاج هذا الضعف إلى مراجعة المشرف بعد محاولات التقوية والتحقق.",
        )
    if prepared.get("journey_completed"):
        return None

    # Early promotion creates a fresh target-level session. Continue this same
    # request on that session so the response and subsequent submit never point
    # at the just-closed historical session.
    prepared_session_id = int(prepared.get("session_id") or session.id)
    if prepared_session_id != session.id:
        session = _activity_session_or_404(db, prepared_session_id, student.id)

    db.refresh(session)
    db.refresh(student)
    level_id = session.assigned_level or student.current_level

    pending_attempt = _pending_attempt(db, session.id)
    if pending_attempt:
        item = _load_item(db, pending_attempt.item_id)
        if not item:
            raise HTTPException(status_code=409, detail="تعذر تحميل نشاط التقوية أو التحقق")
        first_pending = next(
            (step for step in item.steps if not _step_state(db, pending_attempt, step)["done"]),
            None,
        )
        if first_pending:
            return _step_payload(db, item, pending_attempt, first_pending)
        _finalize_attempt_if_done(db, pending_attempt, item)
        db.commit()

    item = _next_unused_core_item(
        db,
        student_id=student.id,
        session_id=session.id,
        level_id=level_id,
    )
    if not item:
        _finalize_session_if_done(db, session, level_id)
        db.commit()
        if session.status == "completed":
            return None
        raise HTTPException(status_code=409, detail="لا يمكن متابعة المسار دون محتوى معتمد مطابق")

    attempt = Attempt(session_id=session.id, item_id=item.id, status="in_progress")
    db.add(attempt)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        attempt = db.query(Attempt).filter(
            Attempt.session_id == session.id,
            Attempt.item_id == item.id,
        ).one()

    first_step = next(iter(item.steps), None)
    if not first_step:
        raise HTTPException(status_code=409, detail="النشاط لا يحتوي على جولات معتمدة")
    return _step_payload(db, item, attempt, first_step)


# Fixed /next is intentionally registered before the legacy router. FastAPI
# matches routes in registration order; all non-/next endpoints remain unchanged.
router.include_router(legacy_activities_router)
