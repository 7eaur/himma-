"""Temporary neutral bypass for voice-recording tasks.

This module exists only so the current recovery build can be tested end-to-end
before the production Arabic speech pipeline is activated. It deliberately
keeps the real upload/review path intact and never creates fake audio or scores.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import assessment
from content_runtime import canonical_interaction
from db.activity_models import ActivityStepResponse
from db.models import (
    AssessmentSession,
    Attempt,
    AttemptResponse,
    AudioReview,
    AudioSubmission,
    ContentItem,
    OperationIdempotency,
    Student,
)
from dependencies import get_current_student, get_db
from runtime_flags import temporary_audio_skip_enabled

router = APIRouter(tags=["Temporary audio testing"])


class TemporaryAudioSkipRequest(BaseModel):
    step_id: int
    elapsed_seconds: int = Field(default=0, ge=0, le=3600)


def _operation(session_id: int, item_id: int, step_id: int) -> str:
    return f"temporary_audio_skip:{session_id}:{item_id}:{step_id}"


def _temporary_skip_markers(db: Session, student_id: int, session_id: int) -> set[tuple[int, int]]:
    rows = db.query(OperationIdempotency).filter(
        OperationIdempotency.actor_role == "student",
        OperationIdempotency.actor_id == student_id,
        OperationIdempotency.operation.like(f"temporary_audio_skip:{session_id}:%"),
    ).all()
    markers: set[tuple[int, int]] = set()
    for row in rows:
        parts = row.operation.split(":")
        if len(parts) != 4:
            continue
        try:
            markers.add((int(parts[2]), int(parts[3])))
        except ValueError:
            continue
    return markers


def _has_temporary_skips(db: Session, student_id: int, session_id: int) -> bool:
    return db.query(OperationIdempotency.id).filter(
        OperationIdempotency.actor_role == "student",
        OperationIdempotency.actor_id == student_id,
        OperationIdempotency.operation.like(f"temporary_audio_skip:{session_id}:%"),
    ).first() is not None


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
    """Complete one recording step as neutral evidence without creating audio."""

    if not temporary_audio_skip_enabled():
        raise HTTPException(status_code=403, detail="التخطي المؤقت للتسجيل غير مفعّل")

    idempotency_key = assessment._validate_idempotency_key(idempotency_key)
    operation = _operation(session_id, item_id, body.step_id)
    request_hash = assessment._request_hash(body.model_dump(mode="json"))
    replay = assessment._idempotency_replay(
        db,
        student.id,
        operation,
        idempotency_key,
        request_hash,
    )
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

    # Reserved neutral sentinel for the temporary demo path:
    # is_correct=None + no AudioSubmission. This makes the existing activity
    # runner treat the step as flow-complete while adaptation/rewards correctly
    # reject it as unresolved academic evidence. The durable idempotency record
    # below carries the explicit temporary_audio_skip marker.
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
    assessment._store_idempotency(
        db,
        student.id,
        operation,
        idempotency_key,
        request_hash,
        response_json,
    )
    return assessment._commit_idempotent(
        db,
        student.id,
        operation,
        idempotency_key,
        request_hash,
        response_json,
    )


def _finish_session_with_neutral_skips(db: Session, student: Student, session: AssessmentSession) -> dict:
    """Finish pre/post tests with temporary recording skips excluded from score."""

    rerecord_exists = db.query(AudioSubmission).join(
        AttemptResponse, AttemptResponse.id == AudioSubmission.response_id,
    ).join(Attempt, Attempt.id == AttemptResponse.attempt_id).filter(
        Attempt.session_id == session.id,
        AudioSubmission.status == "rerecord_required",
    ).first()
    if rerecord_exists:
        raise HTTPException(status_code=409, detail="يوجد تسجيل يحتاج إلى إعادة قبل إنهاء الاختبار")

    required_items = db.query(ContentItem).filter(
        ContentItem.kind == assessment.KIND_BY_SESSION_TYPE[session.session_type],
    ).count()
    attempts = db.query(Attempt).filter(Attempt.session_id == session.id).all()
    if required_items != 30 or len(attempts) != required_items or any(attempt.status != "completed" for attempt in attempts):
        raise HTTPException(status_code=400, detail="أكمل الأسئلة الثلاثين قبل إنهاء الاختبار")

    temporary_markers = _temporary_skip_markers(db, student.id, session.id)
    total_score = Decimal("0.0")
    scorable_units = Decimal("0.0")

    for attempt in attempts:
        responses = db.query(AttemptResponse).filter(AttemptResponse.attempt_id == attempt.id).all()
        for response in responses:
            audio_sub = db.query(AudioSubmission).filter(AudioSubmission.response_id == response.id).first()
            if audio_sub:
                if audio_sub.status == "uploaded":
                    raise HTTPException(status_code=409, detail="يوجد تسجيل صوتي في انتظار المراجعة")
                if audio_sub.status == "graded":
                    review = db.query(AudioReview).filter(
                        AudioReview.submission_id == audio_sub.id,
                    ).order_by(AudioReview.id.desc()).first()
                    if not review:
                        raise HTTPException(status_code=409, detail="تقييم التسجيل الصوتي غير مكتمل")
                    scorable_units += Decimal("1.0")
                    total_score += review.rubric_score
                continue

            marker = (attempt.item_id, response.step_id) in temporary_markers
            if marker and response.is_correct is None:
                # TEMPORARY — intentionally excluded from both numerator and denominator.
                continue
            if response.is_correct is None:
                raise HTTPException(status_code=409, detail="يوجد سؤال غير مكتمل التقييم")
            scorable_units += Decimal("1.0")
            if response.is_correct:
                total_score += Decimal("1.0")

        structured = db.query(ActivityStepResponse).filter(
            ActivityStepResponse.attempt_id == attempt.id,
        ).all()
        for response in structured:
            payload = response.response_payload or {}
            if payload.get("declared_media_gap_skip") or payload.get("temporary_audio_skip"):
                continue
            scorable_units += Decimal("1.0")
            if response.is_correct:
                total_score += Decimal("1.0")

    if scorable_units <= 0:
        raise HTTPException(status_code=409, detail="لا توجد أسئلة قابلة للتقييم في هذه المحاولة")

    final_percentage = (total_score / scorable_units) * Decimal("100.0")
    if final_percentage < Decimal("50.0"):
        assigned_level = 1
    elif final_percentage < Decimal("80.0"):
        assigned_level = 2
    else:
        assigned_level = 3

    session.final_score = final_percentage
    session.assigned_level = assigned_level
    session.status = "completed"
    session.completed_at = datetime.now(timezone.utc)
    session.updated_at = datetime.now(timezone.utc)
    student.current_level = assigned_level
    if session.session_type == "posttest":
        student.posttest_enabled = False
        student.posttest_enabled_at = None
        student.posttest_enabled_by = None
    db.commit()
    return {
        "id": session.id,
        "final_score": final_percentage,
        "assigned_level": assigned_level,
        "temporary_audio_skips": len(temporary_markers),
        "scorable_units": int(scorable_units),
    }


# This route is registered before assessment.router in main.py. Normal sessions
# delegate untouched to the accepted implementation; only sessions containing
# explicit temporary skip markers use the neutral denominator calculation.
@router.post("/assessment/session/{session_id}/finish")
def finish_assessment_with_optional_temporary_skips(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.student_id == student.id,
    ).first()
    if not session or session.status != "in_progress":
        raise HTTPException(status_code=400, detail="الجلسة غير صالحة أو مكتملة")

    if session.session_type not in {"pretest", "posttest"} or not _has_temporary_skips(db, student.id, session.id):
        return assessment.finish_session(session_id=session_id, db=db, student=student)

    return _finish_session_with_neutral_skips(db, student, session)
