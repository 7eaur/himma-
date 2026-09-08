"""Read-only researcher preview of the exact current student content contract.

Preview never creates sessions, attempts, responses, progress, reinforcement
cycles, recordings, or scoring evidence.  It reads the already-published DB
runtime and delegates learner payload construction to the same serializers used
by student-facing contracts.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from content_runtime import canonical_id, canonical_interaction
from content_student_view import activity_student_content, assessment_student_payload
from db.models import ContentItem, ContentRelease, User
from dependencies import get_current_user, get_db

router = APIRouter(prefix="/researcher/content-preview", tags=["Content Preview"])

ASSESSMENT_KINDS = {"pretest_question", "posttest_question"}
LEARNING_KINDS = {"core_activity", "reinforcement_activity"}
ALLOWED_KINDS = ASSESSMENT_KINDS | LEARNING_KINDS


def _query(db: Session):
    return db.query(ContentItem).options(
        joinedload(ContentItem.steps),
        joinedload(ContentItem.assets),
        joinedload(ContentItem.skill),
    )


def _published_items(db: Session) -> list[ContentItem]:
    return sorted(
        [item for item in _query(db).all() if item.status == "approved"],
        key=lambda item: (
            str(item.kind),
            int(item.level_id or 0),
            int(item.order_index or 0),
            int(item.id or 0),
        ),
    )


def _active_release(db: Session) -> dict | None:
    row = db.query(ContentRelease).filter(ContentRelease.is_active.is_(True)).first()
    if row is None:
        return None
    return {"version": row.version, "is_active": bool(row.is_active)}


def _summary(item: ContentItem) -> dict:
    data = item.template_data or {}
    return {
        "id": item.id,
        "canonical_id": canonical_id(item),
        "stable_key": item.stable_key,
        "kind": item.kind,
        "level_id": item.level_id,
        "order_index": item.order_index,
        "interaction_type": canonical_interaction(item),
        "title": data.get("title") or (item.skill.name if item.skill is not None else "مهمة تعليمية"),
        "release_version": data.get("canonical_release_version"),
        "release_sha256": data.get("canonical_release_sha256"),
    }


def _find_by_canonical(db: Session, wanted: str) -> ContentItem:
    normalized = wanted.strip().casefold()
    matches = [
        item
        for item in _published_items(db)
        if canonical_id(item).casefold() == normalized
        or str(item.stable_key).casefold() == normalized
    ]
    if len(matches) != 1:
        raise HTTPException(status_code=404, detail="عنصر المحتوى المطلوب غير موجود")
    return matches[0]


@router.get("")
def list_content_preview(
    kind: str | None = Query(default=None),
    level_id: int | None = Query(default=None, ge=1, le=3),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if kind is not None and kind not in ALLOWED_KINDS:
        raise HTTPException(status_code=400, detail="نوع المحتوى المطلوب غير صالح")
    items = _published_items(db)
    if kind is not None:
        items = [item for item in items if item.kind == kind]
    if level_id is not None:
        items = [item for item in items if int(item.level_id or 0) == level_id]
    return {
        "mode": "read_only",
        "writes_progress": False,
        "active_release": _active_release(db),
        "count": len(items),
        "items": [_summary(item) for item in items],
    }


@router.get("/{canonical_key}")
def get_content_preview(
    canonical_key: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = _find_by_canonical(db, canonical_key)
    steps = sorted(item.steps, key=lambda step: (int(step.order_index), int(step.id or 0)))
    if not steps:
        raise HTTPException(status_code=409, detail="عنصر المحتوى لا يحتوي جولات منشورة")

    if item.kind in ASSESSMENT_KINDS:
        if len(steps) != 1:
            raise HTTPException(status_code=409, detail="عنصر الاختبار يجب أن يحتوي جولة واحدة")
        payload = assessment_student_payload(item, steps[0])
        surface = "assessment"
    elif item.kind in LEARNING_KINDS:
        payload = {
            "item": activity_student_content(item, steps[0])["item"],
            "rounds": [activity_student_content(item, step)["step"] for step in steps],
        }
        surface = "learning"
    else:
        raise HTTPException(status_code=409, detail="نوع المحتوى غير مدعوم في المعاينة")

    return {
        "mode": "read_only",
        "writes_progress": False,
        "surface": surface,
        "summary": _summary(item),
        "payload": payload,
    }
