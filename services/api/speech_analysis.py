"""Researcher-facing control/status API for P07 speech analysis.

Provider execution is deliberately not performed inside HTTP requests. The
worker owns ASR calls; these endpoints expose queue state and explicit retries.
Machine analysis is advisory. Human Supervisor Review is the current academic
authority and is exposed alongside the same immutable AudioSubmission.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from audio_review_state import latest_audio_review
from db.models import AudioSubmission, AuditLog, User
from db.speech_models import SpeechAnalysis, SpeechAnalysisJob
from dependencies import get_current_researcher, get_db
from speech_pipeline import enqueue_submission


router = APIRouter(prefix="/speech-analysis", tags=["Speech Analysis"])


def _human_review_payload(db: Session, submission: AudioSubmission | None) -> dict | None:
    review = latest_audio_review(db, submission)
    if review is None:
        return None
    return {
        "id": review.id,
        "submission_id": review.submission_id,
        "reviewer_id": review.reviewer_id,
        "target_units": review.target_units,
        "deletions": review.deletions,
        "substitutions": review.substitutions,
        "insertions": review.insertions,
        "rubric_score": float(review.rubric_score),
        "supersedes_review_id": review.supersedes_review_id,
        "created_at": review.created_at,
    }


def _analysis_payload(
    db: Session,
    job: SpeechAnalysisJob,
    analysis: SpeechAnalysis | None,
    submission: AudioSubmission | None,
) -> dict:
    human_review = _human_review_payload(db, submission)
    return {
        "job": {
            "id": job.id,
            "submission_id": job.submission_id,
            "status": job.status,
            "attempt_count": job.attempt_count,
            "max_attempts": job.max_attempts,
            "next_attempt_at": job.next_attempt_at,
            "last_error_code": job.last_error_code,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "completed_at": job.completed_at,
        },
        "analysis": None if not analysis else {
            "id": analysis.id,
            "provider_name": analysis.provider_name,
            "provider_model": analysis.provider_model,
            "reference_text": analysis.reference_text,
            "transcript_text": analysis.transcript_text,
            "overall_confidence": float(analysis.overall_confidence) if analysis.overall_confidence is not None else None,
            "decision": analysis.decision,
            "correct_count": analysis.correct_count,
            "deletion_count": analysis.deletion_count,
            "insertion_count": analysis.insertion_count,
            "substitution_count": analysis.substitution_count,
            "duration_seconds": float(analysis.duration_seconds) if analysis.duration_seconds is not None else None,
            "tokens": analysis.tokens_json,
            "calibration_version": analysis.calibration_version,
            "created_at": analysis.created_at,
        },
        "adjudication": {
            "machine_role": "advisory",
            "academic_authority": "human_supervisor",
            "submission_status": submission.status if submission else None,
            "human_review": human_review,
            "academic_decision_available": bool(
                submission is not None
                and submission.status == "graded"
                and human_review is not None
            ),
        },
    }


@router.get("/queue")
def queue_status(
    db: Session = Depends(get_db),
    researcher: User = Depends(get_current_researcher),
):
    jobs = db.query(SpeechAnalysisJob).order_by(
        SpeechAnalysisJob.created_at.desc(), SpeechAnalysisJob.id.desc()
    ).limit(100).all()
    return {
        "items": [
            {
                "id": job.id,
                "submission_id": job.submission_id,
                "status": job.status,
                "attempt_count": job.attempt_count,
                "max_attempts": job.max_attempts,
                "next_attempt_at": job.next_attempt_at,
                "last_error_code": job.last_error_code,
                "updated_at": job.updated_at,
            }
            for job in jobs
        ]
    }


@router.post("/submission/{submission_id}/enqueue")
def enqueue(
    submission_id: int,
    db: Session = Depends(get_db),
    researcher: User = Depends(get_current_researcher),
):
    if not db.query(AudioSubmission.id).filter(AudioSubmission.id == submission_id).first():
        raise HTTPException(status_code=404, detail="Audio submission not found")
    job = enqueue_submission(db, submission_id)
    db.add(AuditLog(
        actor_role="researcher",
        actor_id=researcher.id,
        action="enqueue_speech_analysis",
        entity_type="AudioSubmission",
        entity_id=str(submission_id),
        details=f"Speech job {job.id} status={job.status}",
    ))
    db.commit()
    db.refresh(job)
    return {"job_id": job.id, "status": job.status}


@router.get("/submission/{submission_id}")
def submission_analysis(
    submission_id: int,
    db: Session = Depends(get_db),
    researcher: User = Depends(get_current_researcher),
):
    submission = db.query(AudioSubmission).filter(AudioSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Audio submission not found")
    job = db.query(SpeechAnalysisJob).filter(
        SpeechAnalysisJob.submission_id == submission_id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Speech analysis job not found")
    analysis = db.query(SpeechAnalysis).filter(SpeechAnalysis.job_id == job.id).first()
    return _analysis_payload(db, job, analysis, submission)


@router.post("/job/{job_id}/retry")
def retry_job(
    job_id: int,
    db: Session = Depends(get_db),
    researcher: User = Depends(get_current_researcher),
):
    job = db.query(SpeechAnalysisJob).filter(SpeechAnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Speech analysis job not found")
    if db.query(SpeechAnalysis.id).filter(SpeechAnalysis.job_id == job.id).first():
        raise HTTPException(status_code=409, detail="Completed analysis cannot be retried in place")
    if job.status not in {"failed", "dead_letter", "blocked_provider", "retry_wait"}:
        raise HTTPException(status_code=409, detail="Job is not in a retryable state")

    job.status = "queued"
    job.next_attempt_at = None
    job.last_error_code = None
    job.last_error_message = None
    job.updated_at = datetime.now(timezone.utc)
    db.add(AuditLog(
        actor_role="researcher",
        actor_id=researcher.id,
        action="retry_speech_analysis",
        entity_type="SpeechAnalysisJob",
        entity_id=str(job.id),
        details="Manual queue retry requested",
    ))
    db.commit()
    return {"job_id": job.id, "status": job.status}
