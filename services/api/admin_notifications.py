from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db.models import User
from db.notification_models import ResearcherNotification
from dependencies import get_current_user, get_db

router = APIRouter(prefix="/researcher/notifications", tags=["Researcher Notifications"])


def _payload(notification: ResearcherNotification) -> dict:
    return {
        "id": notification.id,
        "type": notification.notification_type,
        "title": notification.title,
        "message": notification.message,
        "href": notification.href,
        "entity_type": notification.entity_type,
        "entity_id": notification.entity_id,
        "is_read": bool(notification.is_read),
        "created_at": notification.created_at,
        "read_at": notification.read_at,
    }


@router.get("")
def list_notifications(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Read the durable inbox without reconciling or mutating domain state."""
    rows = (
        db.query(ResearcherNotification)
        .order_by(ResearcherNotification.is_read.asc(), ResearcherNotification.created_at.desc(), ResearcherNotification.id.desc())
        .limit(limit)
        .all()
    )
    unread = db.query(ResearcherNotification.id).filter(ResearcherNotification.is_read.is_(False)).count()
    return {"unread_count": unread, "items": [_payload(row) for row in rows]}


@router.post("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = db.query(ResearcherNotification).filter(ResearcherNotification.id == notification_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="الإشعار غير موجود")
    if not row.is_read:
        row.is_read = True
        row.read_at = datetime.now(timezone.utc)
        db.commit()
    return _payload(row)


@router.post("/read-all")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    rows = db.query(ResearcherNotification).filter(ResearcherNotification.is_read.is_(False)).all()
    for row in rows:
        row.is_read = True
        row.read_at = now
    db.commit()
    return {"updated": len(rows)}
