from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal

from dependencies import get_db, get_current_user
from db.models import (
    User, AudioSubmission, Attempt, AttemptResponse, AuditLog, AudioReview
)
import schemas

router = APIRouter(prefix="/review", tags=["Review"])

@router.get("/pending-audio", response_model=List[schemas.AudioSubmissionReviewResponse])
def get_pending_audio(
    db: Session = Depends(get_db),
    researcher: User = Depends(get_current_user)
):
    """Get all audio submissions that need grading."""
    submissions = db.query(AudioSubmission).filter(
        AudioSubmission.status == "uploaded"
    ).all()
    return submissions

@router.post("/audio/{submission_id}/grade")
def grade_audio_submission(
    submission_id: int,
    request: schemas.GradeAudioRequest,
    db: Session = Depends(get_db),
    researcher: User = Depends(get_current_user)
):
    """Grade an audio submission (updates both audio and the response)."""
    submission = db.query(AudioSubmission).filter(AudioSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    response = db.query(AttemptResponse).filter(AttemptResponse.id == submission.response_id).first()
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
        
    if not request.is_valid:
        submission.status = "rerecord_required"
        response.is_correct = None
        attempt = db.query(Attempt).filter(Attempt.id == response.attempt_id).first()
        if not attempt:
            raise HTTPException(status_code=404, detail="Attempt not found")
        attempt.status = "in_progress"
        attempt.completed_at = None
        db.add(AuditLog(
            actor_role="researcher",
            actor_id=researcher.id,
            action="request_audio_rerecord",
            entity_type="AudioSubmission",
            entity_id=str(submission.id),
            details="Recording marked invalid; student attempt reopened",
        ))
        db.commit()
        return {"status": "ok", "message": "Marked for rerecord"}
        
    # Calculate rubric score
    if not request.target_units or request.target_units <= 0:
        raise HTTPException(status_code=400, detail="target_units must be > 0 for valid grading")
        
    if request.deletions + request.substitutions > request.target_units:
        raise HTTPException(status_code=400, detail="deletions + substitutions cannot exceed target_units")
        
    errors = request.deletions + request.substitutions + request.insertions
    rubric_score_val = max(0.0, 1.0 - (errors / request.target_units))
    rubric_score = Decimal(str(rubric_score_val))
    
    submission.status = "graded"
    response.is_correct = True if rubric_score > 0 else False 
    
    # Find existing review to supersede
    existing_review = db.query(AudioReview).filter(
        AudioReview.submission_id == submission.id
    ).order_by(AudioReview.id.desc()).first()
    
    # Create AudioReview
    review = AudioReview(
        submission_id=submission.id,
        reviewer_id=researcher.id,
        target_units=request.target_units,
        deletions=request.deletions,
        substitutions=request.substitutions,
        insertions=request.insertions,
        rubric_score=rubric_score,
        supersedes_review_id=existing_review.id if existing_review else None,
        pronunciation_notes=request.pronunciation_notes,
        fluency_notes=request.fluency_notes,
        time_notes=request.time_notes
    )
    db.add(review)
    
    # Audit log
    audit = AuditLog(
        actor_role="researcher",
        actor_id=researcher.id,
        action="grade_audio",
        entity_type="AudioSubmission",
        entity_id=str(submission.id),
        details=f"Graded score={rubric_score}"
    )
    db.add(audit)
    
    db.commit()
    return {"status": "ok", "rubric_score": float(rubric_score)}
