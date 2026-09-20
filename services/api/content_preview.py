"""Read-only administrative review of the exact approved Himma content.

This endpoint is deliberately NOT a student preview. It reads only approved
PostgreSQL content and exposes the academic truth a supervisor needs to audit:
questions, instructions, hints, canonical options, correct answers, recording
targets and approved media. It never creates sessions, attempts, responses,
recordings, reinforcement cycles or progress.

Student serializers remain separate and continue to hide answer metadata.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from content_runtime import (
    active_options,
    canonical_id,
    canonical_interaction,
    instruction_text,
    item_assets,
    media_gaps,
    presentation_data,
    step_assets,
)
from db.models import ContentItem, ContentRelease, ContentStep, User
from dependencies import get_current_user, get_db

router = APIRouter(prefix="/researcher/content-preview", tags=["Content Review"])

ASSESSMENT_KINDS = {"pretest_question", "posttest_question"}
LEARNING_KINDS = {"core_activity", "reinforcement_activity"}
ALLOWED_KINDS = ASSESSMENT_KINDS | LEARNING_KINDS
READ_INTERACTIONS = {"read_aloud", "timed_read_aloud"}
ORDER_INTERACTIONS = {"sequence", "memory_sequence", "path_sequence", "build_word"}


def _query(db: Session):
    return db.query(ContentItem).options(
        joinedload(ContentItem.steps).joinedload(ContentStep.options),
        joinedload(ContentItem.steps).joinedload(ContentStep.assets),
        joinedload(ContentItem.assets),
        joinedload(ContentItem.skill),
    )


def _sort_key(item: ContentItem) -> tuple[int, int, int]:
    kind = str(item.kind)
    level = int(item.level_id or 0)
    if kind == "pretest_question":
        section = 0
    elif kind == "core_activity":
        section = 10 + (level * 10)
    elif kind == "reinforcement_activity":
        section = 11 + (level * 10)
    elif kind == "posttest_question":
        section = 50
    else:
        section = 99
    return section, int(item.order_index or 0), int(item.id or 0)


def _published_items(db: Session) -> list[ContentItem]:
    return sorted(
        [item for item in _query(db).all() if item.status == "approved"],
        key=_sort_key,
    )


def _active_release(db: Session) -> dict | None:
    row = db.query(ContentRelease).filter(ContentRelease.is_active.is_(True)).first()
    if row is None:
        return None
    return {
        "version": row.version,
        "is_active": bool(row.is_active),
        "released_at": row.released_at.isoformat() if row.released_at else None,
    }


def _context_intro(item: ContentItem) -> dict | None:
    approval = ((item.template_data or {}).get("content_approval_2026_09_08") or {})
    value = approval.get("context_intro")
    return dict(value) if isinstance(value, dict) else None


def _layout_hint(item: ContentItem) -> str | None:
    approval = ((item.template_data or {}).get("content_approval_2026_09_08") or {})
    value = approval.get("layout_hint")
    return str(value) if value else None


def _round_presentation(item: ContentItem, step: ContentStep) -> dict:
    value = presentation_data(item, step)
    return dict(value) if isinstance(value, dict) else {}


def _question_text(item: ContentItem, step: ContentStep) -> str:
    presentation = _round_presentation(item, step)
    return str(presentation.get("question_text") or step.prompt_text or "")


def _answer_contract(item: ContentItem, step: ContentStep) -> dict:
    interaction = canonical_interaction(item)
    options = active_options(step)

    if interaction in READ_INTERACTIONS:
        target = str(step.expected_reading_text or "").strip()
        return {
            "kind": "recording_target",
            "label": "النص المطلوب من الطالب تسجيله",
            "values": [target] if target else [],
            "option_ids": [],
        }

    if interaction in ORDER_INTERACTIONS:
        return {
            "kind": "ordered_sequence",
            "label": "الترتيب الصحيح",
            "values": [str(option.text) for option in options],
            "option_ids": [int(option.id) for option in options],
        }

    correct = [option for option in options if bool(option.is_correct)]
    return {
        "kind": "correct_options" if correct else "none",
        "label": "الإجابة الصحيحة" if len(correct) <= 1 else "الإجابات الصحيحة",
        "values": [str(option.text) for option in correct],
        "option_ids": [int(option.id) for option in correct],
    }


def _review_round(item: ContentItem, step: ContentStep) -> dict:
    presentation = _round_presentation(item, step)
    options = active_options(step)
    stimulus = presentation.get("stimulus")
    if not isinstance(stimulus, dict):
        stimulus = {}
    stimulus_text = str(
        presentation.get("stimulus_text")
        or (stimulus.get("text") if stimulus.get("kind") == "text" else "")
        or ""
    )
    return {
        "id": int(step.id),
        "order_index": int(step.order_index),
        "round_number": int(presentation.get("round_number") or step.order_index),
        "round_total": len(item.steps),
        "question_text": _question_text(item, step),
        "instruction_text": instruction_text(item, step),
        "encouragement": str(presentation.get("encouragement") or ""),
        "hint": str(presentation.get("hint") or ""),
        "stimulus": stimulus,
        "stimulus_text": stimulus_text,
        "expected_reading_text": step.expected_reading_text,
        "options": [
            {
                "id": int(option.id),
                "text": str(option.text),
                "order_index": int(option.order_index),
                "is_correct": bool(option.is_correct),
            }
            for option in options
        ],
        "assets": step_assets(item, step),
        "media_gaps": media_gaps(item, step),
        "answer": _answer_contract(item, step),
    }


def _summary(item: ContentItem) -> dict:
    data = item.template_data or {}
    steps = sorted(item.steps, key=lambda step: (int(step.order_index), int(step.id or 0)))
    all_assets = list(item_assets(item))
    for step in steps:
        all_assets.extend(step_assets(item, step))
    interaction = canonical_interaction(item)
    skill_name = item.skill.name if item.skill is not None else ""
    return {
        "id": int(item.id),
        "canonical_id": canonical_id(item),
        "stable_key": str(item.stable_key),
        "kind": str(item.kind),
        "level_id": int(item.level_id) if item.level_id is not None else None,
        "order_index": int(item.order_index),
        "interaction_type": interaction,
        "title": str(data.get("title") or skill_name or "مهمة تعليمية"),
        "skill": str(skill_name),
        "status": str(item.status),
        "round_count": len(steps),
        "has_audio": any(asset.get("asset_type") == "audio" for asset in all_assets),
        "has_images": any(asset.get("asset_type") == "image" for asset in all_assets),
        "requires_recording": interaction in READ_INTERACTIONS,
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
    kind: Annotated[str | None, Query()] = None,
    level_id: Annotated[int | None, Query(ge=1, le=3)] = None,
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
        "purpose": "admin_content_review",
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

    data = item.template_data or {}
    return {
        "mode": "read_only",
        "purpose": "admin_content_review",
        "writes_progress": False,
        "summary": _summary(item),
        "item": {
            "id": int(item.id),
            "canonical_id": canonical_id(item),
            "stable_key": str(item.stable_key),
            "kind": str(item.kind),
            "level_id": int(item.level_id) if item.level_id is not None else None,
            "order_index": int(item.order_index),
            "interaction_type": canonical_interaction(item),
            "title": str(data.get("title") or (item.skill.name if item.skill is not None else "مهمة تعليمية")),
            "skill": str(item.skill.name if item.skill is not None else ""),
            "criterion": data.get("criterion"),
            "status": str(item.status),
            "layout_hint": _layout_hint(item),
            "context_intro": _context_intro(item),
            "item_assets": item_assets(item),
        },
        "rounds": [_review_round(item, step) for step in steps],
    }
