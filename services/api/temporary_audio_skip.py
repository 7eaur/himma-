"""Development-only neutral bypass for student recording tasks.

This module intentionally owns no assessment scoring, placement, mastery, or
completion policy. It creates a neutral persisted response only when the
explicit development runtime flag is enabled. Trial/production fail closed via
runtime_flags.validate_runtime_safety().
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import assessment
from content_runtime import canonical_interaction
from db.activity_models import ActivityStepResponse
from db.models import Attempt, AttemptResponse, Student
from dependencies import get_current_student, get_db
from runtime_flags import temporary_audio_skip_enabled

router = APIRouter(tags=["Development audio bypass"])


class TemporaryAudioSkipRequest(BaseModel):
    step_id: int
    elapsed_seconds: int = Field(default=0, ge=0, le=3600)


def _operation(session_id: int, item_id: int, step_id: int) -> str:
    return f"temporary_audio_skip:{session_id}:{item_id}:{step_id}"


@router.get("/runtime-flags")
def runtime_flags():
    return {
        "temporary_audio_skip": temporary_audio_skip_enabled(),
        "temporary_audio_skip_label": "تخطي مؤقتًا",
    }


@router.post("/temporary-audio/session/{session_id}/attempt/{item_id}/skip")
def skip_recording_task(
    session_id: int,
    item_id: int,
    body: TemporaryAudioSkipRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    if not temporary_audio_skip_enabled():
        raise HTTPException(status_code=403, detail="التخطي المؤقت للتسجيل غير مفعّل")

    idempotency_key = assessment._validate_idempotency_key(idempotency_key)
    operation = _operation(session_id, item_id, body.step_id)
    request_hash = assessment._request_hash(body.model_dump(mode="json"))
    replay = assessment._idempotency_replay(db, student.id, operation, idempotency_key, request_hash)
    if replay is not None:
        return replay

    session = assessment._session_for_student(db, session_id, student.id)
    attempt = db.query(Attempt).filter(
        Attempt.session_id == session.id,
        Attempt.item_id == item_id,
        Attempt.status == "in_progress",
    ).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="لا توجد محاولة تسجيل نشطة لهذه المهمة")

    item = assessment._load_item(db, item_id)
    step = next((candidate for candidate in (item.steps if item else []) if candidate.id == body.step_id), None)
    if not item or not step:
        raise HTTPException(status_code=400, detail="مهمة التسجيل أو خطوتها غير صالحة")
    if canonical_interaction(item) not in assessment.AUDIO_INTERACTIONS:
        raise HTTPException(status_code=400, detail="التخطي المؤقت متاح لمهام التسجيل فقط")

    existing_response = db.query(AttemptResponse).filter(
        AttemptResponse.attempt_id == attempt.id,
        AttemptResponse.step_id == step.id,
    ).first()
    existing_structured = db.query(ActivityStepResponse.id).filter(
        ActivityStepResponse.attempt_id == attempt.id,
        ActivityStepResponse.step_id == step.id,
    ).first()
    if existing_response or existing_structured:
        raise HTTPException(status_code=409, detail="تم إكمال هذه المهمة مسبقًا")

    # Neutral sentinel: no fake audio object, score, review, reward, or mastery
    # evidence is created. Assessment completion recognises the explicit
    # idempotency marker and excludes this unit from the academic denominator.
    db.add(AttemptResponse(
        attempt_id=attempt.id,
        step_id=step.id,
        selected_option_id=None,
        is_correct=None,
        elapsed_seconds=body.elapsed_seconds,
    ))
    db.flush()

    if assessment._completed_response_count(db, attempt.id) >= len(item.steps):
        attempt.status = "completed"
        attempt.completed_at = datetime.now(timezone.utc)
    attempt.elapsed_seconds += body.elapsed_seconds
    session.elapsed_seconds += body.elapsed_seconds
    session.updated_at = datetime.now(timezone.utc)

    response_json = {
        "status": "ok",
        "is_correct": None,
        "temporary_audio_skip": True,
        "academically_neutral": True,
    }
    assessment._store_idempotency(db, student.id, operation, idempotency_key, request_hash, response_json)
    return assessment._commit_idempotent(
        db,
        student.id,
        operation,
        idempotency_key,
        request_hash,
        response_json,
    )
