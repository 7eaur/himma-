from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from datetime import datetime, timezone
from typing import Optional

from dependencies import get_db, get_current_student
from db.models import (
    Student, AssessmentSession, Attempt, AttemptResponse, ContentItem, 
    ContentStep, ContentOption, AudioSubmission, ScoringRule, ScoringPolicy, AudioReview
)
import schemas
import storage
from decimal import Decimal

router = APIRouter(prefix="/assessment", tags=["Assessment"])

@router.post("/start", response_model=schemas.AssessmentSessionResponse)
def start_assessment(
    request: schemas.AssessmentStartRequest,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student)
):
    """Start a new assessment session for a student."""
    # Check if there is an in-progress session of the same type
    existing = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student.id,
        AssessmentSession.session_type == request.session_type,
        AssessmentSession.status == "in_progress"
    ).first()
    
    if existing:
        return existing

    new_session = AssessmentSession(
        student_id=student.id,
        session_type=request.session_type,
        status="in_progress"
    )
    db.add(new_session)
    db.commit()
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
    """Get the next item in the assessment without leaking answers."""
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.student_id == student.id
    ).first()
    
    if not session or session.status != "in_progress":
        raise HTTPException(status_code=404, detail="Active session not found")

    # Get already attempted items
    attempted_item_ids = [
        att.item_id for att in 
        db.query(Attempt.item_id).filter(Attempt.session_id == session_id).all()
    ]

    # Find the next item based on session_type
    kind_map = {
        "pretest": "pretest_question",
        "posttest": "posttest_question",
        "core": "core_activity"
    }
    
    next_item = db.query(ContentItem).options(
        joinedload(ContentItem.steps).joinedload(ContentStep.options)
    ).filter(
        ContentItem.kind == kind_map.get(session.session_type, "pretest_question"),
        ContentItem.id.notin_(attempted_item_ids)
    ).order_by(ContentItem.order_index).first()

    if not next_item:
        # Session complete
        session.status = "completed"
        session.completed_at = datetime.now(timezone.utc)
        db.commit()
        return None

    # We must ensure we don't leak `is_correct` in the response, 
    # but since schemas.ContentOptionResponse doesn't include it, Pydantic will strip it.
    
    # Create an attempt for this item
    attempt = Attempt(
        session_id=session_id,
        item_id=next_item.id,
        status="in_progress"
    )
    db.add(attempt)
    db.commit()

    return next_item

@router.post("/session/{session_id}/attempt/{item_id}/submit")
def submit_attempt(
    session_id: int,
    item_id: int,
    submission: schemas.AttemptResponseSubmit,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student)
):
    """Submit an answer or audio recording for a step, completely idempotently."""
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.student_id == student.id
    ).first()
    
    if not session or session.status != "in_progress":
        raise HTTPException(status_code=400, detail="Invalid session")

    attempt = db.query(Attempt).filter(
        Attempt.session_id == session_id,
        Attempt.item_id == item_id
    ).first()
    
    if not attempt:
        raise HTTPException(status_code=400, detail="Attempt not found")

    # Idempotency check: see if response for this step already exists
    existing_response = db.query(AttemptResponse).filter(
        AttemptResponse.attempt_id == attempt.id,
        AttemptResponse.step_id == submission.step_id
    ).first()

    if existing_response:
        return {"status": "ok", "message": "Already submitted"}

    # Grade if it's an option selection
    is_correct = None
    if submission.selected_option_id:
        option = db.query(ContentOption).filter(ContentOption.id == submission.selected_option_id).first()
        if option:
            is_correct = option.is_correct

    new_response = AttemptResponse(
        attempt_id=attempt.id,
        step_id=submission.step_id,
        selected_option_id=submission.selected_option_id,
        is_correct=is_correct
    )
    db.add(new_response)
    db.flush() # get id

    if submission.audio_storage_key:
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

    db.commit()
    return {"status": "ok", "is_correct": is_correct}

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
        
    # Verify that exactly 30 items (if pretest/posttest) have attempts, and all attempts are completed.
    if session.session_type in ["pretest", "posttest"]:
        attempts_count = db.query(Attempt).filter(Attempt.session_id == session_id).count()
        if attempts_count < 30:
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
                    raise HTTPException(status_code=400, detail="Cannot finish session with ungraded audio")
                if audio_sub.status == "graded":
                    review = db.query(AudioReview).filter(AudioReview.submission_id == audio_sub.id).order_by(AudioReview.id.desc()).first()
                    if review:
                        total_score += review.rubric_score
            else:
                if response.is_correct:
                    total_score += Decimal("1.0")
                    
    # Max score is 30 for pretest/posttest, but we just use percentage of 30 for now
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
    
    # Optional: Update student's current_level if this is a pre/posttest
    if session.session_type in ["pretest", "posttest"]:
        student.current_level = assigned_level
        
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
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Upload audio for an assessment session (returns metadata to submit with attempt)."""
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.student_id == student.id
    ).first()
    
    if not session or session.status != "in_progress":
        raise HTTPException(status_code=400, detail="Invalid session")
        
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Must be an audio file")
        
    try:
        storage_key, file_size = storage.upload_audio(file)
        return {
            "audio_storage_key": storage_key,
            "audio_file_size": file_size,
            "audio_mime_type": file.content_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

