"""Serialized, bounded supervisor claims for V2 human review.

Claims are advisory when absent (a historical unclaimed review still works).
Once a supervisor claims a response, others cannot grade or request a revision
until release/expiry. Every mutation uses the same locked response row first.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.learning_models import AssessmentQuestionResponse, LessonQuestionResponse, V2ReviewClaim
from db.models import AuditLog, User
from dependencies import get_current_user, get_db

router = APIRouter(prefix="/v2/review-claims", tags=["v2-review-claims"])
CLAIM_MINUTES = 10


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _claim(db: Session, kind: Literal["lesson", "assessment"], response_id: int) -> V2ReviewClaim | None:
    key = "lesson_response_id" if kind == "lesson" else "assessment_response_id"
    return db.query(V2ReviewClaim).filter(getattr(V2ReviewClaim, key) == response_id).with_for_update().one_or_none()


def enforce_review_claim(db: Session, kind: Literal["lesson", "assessment"], response_id: int, reviewer_id: int) -> None:
    claim = _claim(db, kind, response_id)
    if claim and _aware(claim.expires_at) > datetime.now(timezone.utc) and claim.reviewer_id != reviewer_id:
        raise HTTPException(status_code=409, detail="الإجابة محجوزة لمشرف آخر؛ حدّث قائمة المراجعة")


def clear_review_claim(db: Session, kind: Literal["lesson", "assessment"], response_id: int) -> None:
    claim = _claim(db, kind, response_id)
    if claim:
        claim.expires_at = datetime.now(timezone.utc)


def _response(db: Session, kind: Literal["lesson", "assessment"], response_id: int):
    model = LessonQuestionResponse if kind == "lesson" else AssessmentQuestionResponse
    row = db.query(model).filter(model.id == response_id).with_for_update().one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="إجابة المراجعة غير موجودة")
    if row.status != "pending_review":
        raise HTTPException(status_code=409, detail="هذه الإجابة لم تعد تنتظر مراجعة")
    return row


@router.post("/admin/{kind}/{response_id}/claim")
def claim_review(
    kind: Literal["lesson", "assessment"], response_id: int,
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    _response(db, kind, response_id)
    enforce_review_claim(db, kind, response_id, user.id)
    now = datetime.now(timezone.utc)
    claim = _claim(db, kind, response_id)
    if claim is None:
        claim = V2ReviewClaim(
            lesson_response_id=response_id if kind == "lesson" else None,
            assessment_response_id=response_id if kind == "assessment" else None,
            reviewer_id=user.id, claimed_at=now,
            expires_at=now + timedelta(minutes=CLAIM_MINUTES),
        )
        db.add(claim)
    else:
        claim.reviewer_id = user.id
        claim.claimed_at = now
        claim.expires_at = now + timedelta(minutes=CLAIM_MINUTES)
    db.flush()
    db.add(AuditLog(
        actor_role="researcher", actor_id=user.id, action="v2_review_claimed",
        entity_type=kind, entity_id=str(response_id), details="time_limited_10_minutes",
    ))
    db.commit()
    return {"status": "claimed", "kind": kind, "response_id": response_id,
            "expires_at": claim.expires_at.isoformat()}


@router.delete("/admin/{kind}/{response_id}/claim")
def release_review_claim(
    kind: Literal["lesson", "assessment"], response_id: int,
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    _response(db, kind, response_id)
    enforce_review_claim(db, kind, response_id, user.id)
    clear_review_claim(db, kind, response_id)
    db.add(AuditLog(
        actor_role="researcher", actor_id=user.id, action="v2_review_claim_released",
        entity_type=kind, entity_id=str(response_id), details="manual_release",
    ))
    db.commit()
    return {"status": "released", "kind": kind, "response_id": response_id}
