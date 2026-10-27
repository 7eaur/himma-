"""Auditable reviewer acknowledgement for the current V2 reading recording.

This records that the browser reported playback completion. It deliberately
does not claim to prove the reviewer's attention or listening quality.
"""
from __future__ import annotations

from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.models import AuditLog


PLAYBACK_COMPLETED_ACTION = "v2_review_audio_playback_completed"


class AudioPlaybackCompletion(BaseModel):
    audio_submission_id: int = Field(gt=0)


def _entity_type(kind: Literal["lesson", "assessment"]) -> str:
    return f"{kind}_question_response"


def audio_playback_completed(
    db: Session, *, kind: Literal["lesson", "assessment"], response_id: int,
    audio_submission_id: int, reviewer_id: int,
) -> bool:
    return db.query(AuditLog.id).filter(
        AuditLog.actor_role == "researcher",
        AuditLog.actor_id == reviewer_id,
        AuditLog.action == PLAYBACK_COMPLETED_ACTION,
        AuditLog.entity_type == _entity_type(kind),
        AuditLog.entity_id == str(response_id),
        AuditLog.details == f"audio_submission_id={audio_submission_id}",
    ).first() is not None


def completed_audio_ids(
    db: Session, *, kind: Literal["lesson", "assessment"],
    response_audio_ids: dict[int, int], reviewer_id: int,
) -> set[int]:
    """Load queue acknowledgement state in one query, not one per row."""
    if not response_audio_ids:
        return set()
    rows = db.query(AuditLog.entity_id, AuditLog.details).filter(
        AuditLog.actor_role == "researcher",
        AuditLog.actor_id == reviewer_id,
        AuditLog.action == PLAYBACK_COMPLETED_ACTION,
        AuditLog.entity_type == _entity_type(kind),
        AuditLog.entity_id.in_([str(response_id) for response_id in response_audio_ids]),
    ).all()
    completed: set[int] = set()
    for entity_id, details in rows:
        try:
            response_id = int(entity_id)
        except (TypeError, ValueError):
            continue
        audio_id = response_audio_ids.get(response_id)
        if audio_id is not None and details == f"audio_submission_id={audio_id}":
            completed.add(audio_id)
    return completed


def acknowledge_audio_playback(
    db: Session, *, kind: Literal["lesson", "assessment"], response_id: int,
    audio_submission_id: int, reviewer_id: int,
) -> bool:
    """Add an idempotent audit acknowledgement for this exact audio revision."""
    if audio_playback_completed(
        db, kind=kind, response_id=response_id,
        audio_submission_id=audio_submission_id, reviewer_id=reviewer_id,
    ):
        return False
    db.add(AuditLog(
        actor_role="researcher",
        actor_id=reviewer_id,
        action=PLAYBACK_COMPLETED_ACTION,
        entity_type=_entity_type(kind),
        entity_id=str(response_id),
        details=f"audio_submission_id={audio_submission_id}",
    ))
    return True


def require_audio_playback(
    db: Session, *, kind: Literal["lesson", "assessment"], response_id: int,
    audio_submission_id: int, reviewer_id: int,
) -> None:
    if not audio_playback_completed(
        db, kind=kind, response_id=response_id,
        audio_submission_id=audio_submission_id, reviewer_id=reviewer_id,
    ):
        raise HTTPException(
            status_code=409,
            detail="أكمل تشغيل التسجيل الحالي قبل إصدار قرار المراجعة",
        )
