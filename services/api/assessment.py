import hashlib
import json
import re
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from dependencies import get_db, get_current_student
from db.models import (
    AudioReview,
    AudioSubmission,
    AssessmentSession,
    Attempt,
    AttemptResponse,
    ContentItem,
    ContentOption,
    ContentStep,
    OperationIdempotency,
    Student,
)
import schemas
import storage

router = APIRouter(prefix="/assessment", tags=["Assessment"])

KIND_BY_SESSION_TYPE = {
    "pretest": "pretest_question",
    "posttest": "posttest_question",
}

IDEMPOTENCY_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{16,128}$")


def _validate_idempotency_key(value: str) -> str:
    if not IDEMPOTENCY_KEY_PATTERN.fullmatch(value):
        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key must be 16-128 safe characters",
        )
    return value


def _request_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _idempotency_replay(
    db: Session,
    student_id: int,
    operation: str,
    idempotency_key: str,
    request_hash: str,
) -> Optional[dict]:
    record = db.query(OperationIdempotency).filter(
        OperationIdempotency.actor_role == "student",
        OperationIdempotency.actor_id == student_id,
        OperationIdempotency.operation == operation,
        OperationIdempotency.idempotency_key == idempotency_key,
    ).first()
    if not record:
        return None
    if record.request_hash != request_hash:
        raise HTTPException(
            status_code=409,
            detail="Idempotency-Key was already used with a different request",
        )
    return record.response_json


def _store_idempotency(
    db: Session,
    student_id: int,
    operation: str,
    idempotency_key: str,
    request_hash: str,
    response_json: dict,
) -> None:
    db.add(OperationIdempotency(
        actor_role="student",
        actor_id=student_id,
        operation=operation,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
        response_json=response_json,
        status_code=200,
    ))


def _commit_idempotent(
    db: Session,
    student_id: int,
    operation: str,
    idempotency_key: str,
    request_hash: str,
    response_json: dict,
) -> dict:
    try:
        db.commit()
        return response_json
    except IntegrityError:
        db.rollback()
        replay = _idempotency_replay(
            db, student_id, operation, idempotency_key, request_hash
        )
        if replay is not None:
            return replay
        raise HTTPException(status_code=409, detail="Concurrent submission conflict")


def _session_for_student(
    db: Session,
    session_id: int,
    student_id: int,
    *,
    require_active: bool = True,
) -> AssessmentSession:
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.student_id == student_id,
    ).first()
    if not session or (require_active and session.status != "in_progress"):
        raise HTTPException(status_code=404, detail="Active session not found")
    return session


def _item_step_payload(item: ContentItem, step: ContentStep) -> dict:
    return {
        "id": item.id,
        "stable_key": item.stable_key,
        "kind": item.kind,
        "interaction_type": item.interaction_type,
        "template_data": item.template_data,
        "steps": [{
            "id": step.id,
            "order_index": step.order_index,
            "prompt_text": step.prompt_text,
            "expected_reading_text": step.expected_reading_text,
            "options": [
                {"id": option.id, "text": option.text, "order_index": option.order_index}
                for option in step.options
            ],
        }],
    }

@router.post("/start", response_model=schemas.AssessmentSessionResponse)
def start_assessment(
    request: schemas.AssessmentStartRequest,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student)
):
    """Start or resume the single eligible pre/post assessment."""
    if not student.is_active:
        raise HTTPException(status_code=403, detail="Student account is inactive")

    active = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student.id,
        AssessmentSession.status == "in_progress",
    ).first()
    if active:
        if active.session_type == request.session_type:
            return active
        raise HTTPException(status_code=409, detail="Resume the active assessment first")

    completed = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student.id,
        AssessmentSession.session_type == request.session_type,
        AssessmentSession.status == "completed",
    ).first()
    if completed:
        raise HTTPException(status_code=409, detail="This assessment is already completed")

    if request.session_type == "posttest":
        pretest_completed = db.query(AssessmentSession.id).filter(
            AssessmentSession.student_id == student.id,
            AssessmentSession.session_type == "pretest",
            AssessmentSession.status == "completed",
        ).first()
        if not pretest_completed:
            raise HTTPException(status_code=409, detail="Complete the pretest first")
        if not student.posttest_enabled:
            raise HTTPException(status_code=403, detail="The researcher has not enabled the posttest")

    new_session = AssessmentSession(
        student_id=student.id,
        session_type=request.session_type,
        status="in_progress"
    )
    db.add(new_session)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        active = db.query(AssessmentSession).filter(
            AssessmentSession.student_id == student.id,
            AssessmentSession.status == "in_progress",
        ).first()
        if active and active.session_type == request.session_type:
            return active
        raise HTTPException(status_code=409, detail="Assessment lifecycle conflict")
    db.refresh(new_session)
    return new_session

@router.get("/active", response_model=Optional[schemas.AssessmentSessionResponse])
def get_active_session(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student)
):
    """Get the current active session for resume."""
    session = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student.id,
        AssessmentSession.status == "in_progress"
    ).first()
    return session

@router.get("/session/{session_id}/next", response_model=Optional[schemas.ContentItemResponse])
def get_next_item(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student)
):
    """Return exactly one unanswered task without leaking answer keys."""
    session = _session_for_student(db, session_id, student.id)

    pending_attempt = db.query(Attempt).filter(
        Attempt.session_id == session_id,
        Attempt.status == "in_progress",
    ).order_by(Attempt.id).first()
    if pending_attempt:
        item = db.query(ContentItem).options(
            joinedload(ContentItem.steps).joinedload(ContentStep.options)
        ).filter(ContentItem.id == pending_attempt.item_id).first()
        answered_step_ids = {
            row.step_id
            for row in db.query(AttemptResponse.step_id).outerjoin(
                AudioSubmission,
                AudioSubmission.response_id == AttemptResponse.id,
            ).filter(
                AttemptResponse.attempt_id == pending_attempt.id,
                or_(
                    AudioSubmission.id.is_(None),
                    AudioSubmission.status != "rerecord_required",
                ),
            ).all()
        }
        next_step = next(
            (step for step in item.steps if step.id not in answered_step_ids),
            None,
        )
        if next_step:
            return _item_step_payload(item, next_step)

        # Reconcile an interrupted commit where every step exists but the
        # attempt status was not updated yet.
        pending_attempt.status = "completed"
        pending_attempt.completed_at = datetime.now(timezone.utc)
        db.commit()

    # Completed items must not be offered again.
    attempted_item_ids = [
        att.item_id for att in 
        db.query(Attempt.item_id).filter(
            Attempt.session_id == session_id,
            Attempt.status == "completed",
        ).all()
    ]

    next_item = db.query(ContentItem).options(
        joinedload(ContentItem.steps).joinedload(ContentStep.options)
    ).filter(
        ContentItem.kind == KIND_BY_SESSION_TYPE[session.session_type],
        ContentItem.id.notin_(attempted_item_ids)
    ).order_by(ContentItem.order_index).first()

    if not next_item:
        return None

    attempt = Attempt(
        session_id=session_id,
        item_id=next_item.id,
        status="in_progress"
    )
    db.add(attempt)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        attempt = db.query(Attempt).filter(
            Attempt.session_id == session_id,
            Attempt.item_id == next_item.id,
        ).one()

    first_step = next(iter(next_item.steps), None)
    if not first_step:
        raise HTTPException(status_code=409, detail="Content item has no steps")
    return _item_step_payload(next_item, first_step)


@router.get(
    "/session/{session_id}/progress",
    response_model=schemas.AssessmentProgressResponse,
)
def get_session_progress(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = _session_for_student(db, session_id, student.id)

    completed_items = db.query(Attempt).filter(
        Attempt.session_id == session_id,
        Attempt.status == "completed",
    ).count()
    has_pending_item = db.query(Attempt).filter(
        Attempt.session_id == session_id,
        Attempt.status == "in_progress",
    ).first() is not None
    total_items = db.query(ContentItem).filter(
        ContentItem.kind == KIND_BY_SESSION_TYPE[session.session_type],
    ).count()
    completed_steps = db.query(AttemptResponse).join(
        Attempt, Attempt.id == AttemptResponse.attempt_id,
    ).filter(Attempt.session_id == session_id).count()
    total_steps = db.query(func.count(ContentStep.id)).join(
        ContentItem, ContentItem.id == ContentStep.item_id,
    ).filter(
        ContentItem.kind == KIND_BY_SESSION_TYPE[session.session_type],
    ).scalar() or 0
    return {
        "completed_items": completed_items,
        "total_items": total_items,
        "completed_steps": completed_steps,
        "total_steps": total_steps,
        "has_pending_item": has_pending_item,
        "elapsed_seconds": session.elapsed_seconds,
    }

@router.post("/session/{session_id}/attempt/{item_id}/submit")
def submit_attempt(
    session_id: int,
    item_id: int,
    submission: schemas.AttemptResponseSubmit,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    """Submit one step with durable replay protection and timing."""
    idempotency_key = _validate_idempotency_key(idempotency_key)
    operation = f"assessment.answer:{session_id}:{item_id}"
    request_hash = _request_hash(submission.model_dump(mode="json"))
    replay = _idempotency_replay(
        db, student.id, operation, idempotency_key, request_hash
    )
    if replay is not None:
        return replay

    session = _session_for_student(db, session_id, student.id)

    attempt = db.query(Attempt).filter(
        Attempt.session_id == session_id,
        Attempt.item_id == item_id
    ).first()
    
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    item = db.query(ContentItem).filter(ContentItem.id == item_id).first()
    step = db.query(ContentStep).filter(
        ContentStep.id == submission.step_id,
        ContentStep.item_id == item_id,
    ).first()
    if not item or not step:
        raise HTTPException(status_code=400, detail="Step does not belong to this attempt")

    existing_response = db.query(AttemptResponse).filter(
        AttemptResponse.attempt_id == attempt.id,
        AttemptResponse.step_id == submission.step_id
    ).first()

    is_correct = None
    is_audio_item = item.interaction_type in {"read_aloud", "audio_record"}
    if is_audio_item:
        if submission.selected_option_id is not None or not submission.audio_storage_key:
            raise HTTPException(status_code=400, detail="Audio response is required for this item")
        expected_prefix = f"audio/{student.id}/"
        if not submission.audio_storage_key.startswith(expected_prefix):
            raise HTTPException(status_code=403, detail="Audio key does not belong to this student")
        if submission.audio_file_size is None:
            raise HTTPException(status_code=400, detail="Audio file size is required")
        if not (submission.audio_mime_type or "").startswith("audio/"):
            raise HTTPException(status_code=400, detail="Invalid audio MIME type")
        try:
            storage.verify_audio(
                submission.audio_storage_key,
                submission.audio_file_size,
                submission.audio_mime_type,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except RuntimeError:
            raise HTTPException(status_code=503, detail="Audio storage is unavailable")

        if existing_response:
            audio = db.query(AudioSubmission).filter(
                AudioSubmission.response_id == existing_response.id,
            ).first()
            if not audio or audio.status != "rerecord_required":
                raise HTTPException(
                    status_code=409,
                    detail="This step was already submitted; reload to resume",
                )

            audio.storage_key = submission.audio_storage_key
            audio.file_size = submission.audio_file_size
            audio.mime_type = submission.audio_mime_type
            audio.duration_seconds = submission.audio_duration_seconds
            audio.status = "uploaded"
            audio.submitted_at = datetime.now(timezone.utc)
            existing_response.is_correct = None
            existing_response.submitted_at = datetime.now(timezone.utc)
            existing_response.elapsed_seconds += submission.elapsed_seconds
            attempt.elapsed_seconds += submission.elapsed_seconds
            attempt.status = "completed"
            attempt.completed_at = datetime.now(timezone.utc)
            session.elapsed_seconds += submission.elapsed_seconds
            session.updated_at = datetime.now(timezone.utc)
            response_json = {
                "status": "ok",
                "message": "Rerecord submitted",
                "is_correct": None,
            }
            _store_idempotency(
                db,
                student.id,
                operation,
                idempotency_key,
                request_hash,
                response_json,
            )
            return _commit_idempotent(
                db,
                student.id,
                operation,
                idempotency_key,
                request_hash,
                response_json,
            )
    else:
        if existing_response:
            raise HTTPException(
                status_code=409,
                detail="This step was already submitted; reload to resume",
            )
        if submission.audio_storage_key or submission.selected_option_id is None:
            raise HTTPException(status_code=400, detail="A selected option is required for this item")
        option = db.query(ContentOption).filter(
            ContentOption.id == submission.selected_option_id,
            ContentOption.step_id == submission.step_id,
        ).first()
        if not option:
            raise HTTPException(status_code=400, detail="Option does not belong to this step")
        is_correct = option.is_correct

    new_response = AttemptResponse(
        attempt_id=attempt.id,
        step_id=submission.step_id,
        selected_option_id=submission.selected_option_id,
        is_correct=is_correct,
        elapsed_seconds=submission.elapsed_seconds,
    )
    db.add(new_response)
    db.flush() # get id

    if is_audio_item:
        audio = AudioSubmission(
            response_id=new_response.id,
            storage_key=submission.audio_storage_key,
            file_size=submission.audio_file_size or 0,
            mime_type=submission.audio_mime_type or "audio/webm",
            duration_seconds=submission.audio_duration_seconds
        )
        db.add(audio)

    # Check if all steps are completed
    total_steps = db.query(ContentStep).filter(ContentStep.item_id == item_id).count()
    completed_steps = db.query(AttemptResponse).filter(AttemptResponse.attempt_id == attempt.id).count()
    
    if completed_steps >= total_steps:
        attempt.status = "completed"
        attempt.completed_at = datetime.now(timezone.utc)

    attempt.elapsed_seconds += submission.elapsed_seconds
    session.elapsed_seconds += submission.elapsed_seconds
    session.updated_at = datetime.now(timezone.utc)
    response_json = {"status": "ok", "is_correct": is_correct}
    _store_idempotency(
        db,
        student.id,
        operation,
        idempotency_key,
        request_hash,
        response_json,
    )
    return _commit_idempotent(
        db,
        student.id,
        operation,
        idempotency_key,
        request_hash,
        response_json,
    )

@router.post("/session/{session_id}/finish", response_model=schemas.SessionFinishResponse)
def finish_session(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student)
):
    """Finish the session and compute the final score and level."""
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.student_id == student.id
    ).first()
    
    if not session or session.status != "in_progress":
        raise HTTPException(status_code=400, detail="Invalid session")

    rerecord_exists = db.query(AudioSubmission).join(
        AttemptResponse, AttemptResponse.id == AudioSubmission.response_id,
    ).join(
        Attempt, Attempt.id == AttemptResponse.attempt_id,
    ).filter(
        Attempt.session_id == session_id,
        AudioSubmission.status == "rerecord_required",
    ).first()
    if rerecord_exists:
        raise HTTPException(
            status_code=409,
            detail="Cannot finish session with audio requiring rerecord",
        )
        
    # Verify that exactly 30 items (if pretest/posttest) have attempts, and all attempts are completed.
    if session.session_type in ["pretest", "posttest"]:
        required_items = db.query(ContentItem).filter(
            ContentItem.kind == KIND_BY_SESSION_TYPE[session.session_type],
        ).count()
        attempts = db.query(Attempt).filter(Attempt.session_id == session_id).all()
        if required_items != 30 or len(attempts) != required_items or any(
            attempt.status != "completed" for attempt in attempts
        ):
            raise HTTPException(status_code=400, detail="Cannot finish session before completing all 30 items")
            
    # Sum up score securely on backend using Decimal
    total_score = Decimal("0.0")
    attempts = db.query(Attempt).filter(Attempt.session_id == session_id).all()
    for attempt in attempts:
        responses = db.query(AttemptResponse).filter(AttemptResponse.attempt_id == attempt.id).all()
        for response in responses:
            audio_sub = db.query(AudioSubmission).filter(AudioSubmission.response_id == response.id).first()
            if audio_sub:
                if audio_sub.status == "uploaded":
                    raise HTTPException(status_code=409, detail="Cannot finish session with ungraded audio")
                if audio_sub.status == "graded":
                    review = db.query(AudioReview).filter(AudioReview.submission_id == audio_sub.id).order_by(AudioReview.id.desc()).first()
                    if review:
                        total_score += review.rubric_score
            else:
                if response.is_correct:
                    total_score += Decimal("1.0")
                    
    # The approved pre/post contract fixes the assessment denominator at 30 items.
    final_percentage = (total_score / Decimal("30.0")) * Decimal("100.0")
    
    # Assign level based on exact percentage
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
    
    # Optional: Update student's current_level if this is a pre/posttest
    if session.session_type in ["pretest", "posttest"]:
        student.current_level = assigned_level
    if session.session_type == "posttest":
        student.posttest_enabled = False
        student.posttest_enabled_at = None
        student.posttest_enabled_by = None
        
    db.commit()
    
    return {
        "id": session.id,
        "final_score": final_percentage,
        "assigned_level": assigned_level
    }

@router.post("/session/{session_id}/upload-audio")
def upload_audio_submission(
    session_id: int,
    file: UploadFile = File(...),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """Upload audio for an assessment session (returns metadata to submit with attempt)."""
    idempotency_key = _validate_idempotency_key(idempotency_key)
    _session_for_student(db, session_id, student.id)

    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Must be an audio file")

    operation = f"assessment.audio.upload:{session_id}"
    try:
        storage_key, file_size, digest = storage.upload_audio(
            file, student.id, f"{session_id}:{idempotency_key}"
        )
        request_hash = _request_hash({
            "sha256": digest,
            "content_type": file.content_type,
            "file_size": file_size,
        })
        replay = _idempotency_replay(
            db, student.id, operation, idempotency_key, request_hash
        )
        if replay is not None:
            return replay
        response_json = {
            "audio_storage_key": storage_key,
            "audio_file_size": file_size,
            "audio_mime_type": file.content_type,
        }
        _store_idempotency(
            db,
            student.id,
            operation,
            idempotency_key,
            request_hash,
            response_json,
        )
        return _commit_idempotent(
            db,
            student.id,
            operation,
            idempotency_key,
            request_hash,
            response_json,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Audio storage is unavailable")
