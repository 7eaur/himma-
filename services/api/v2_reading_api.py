"""Student-safe speech progress and supervisor-only reading results.

This replaces manual-review display contracts in the V2 rebuild branch.
No API route grants a grade, exposes raw ASR, or mutates student audio.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

import recordings
from db.models import Student, User
from dependencies import get_current_student, get_current_user, get_db
from v2_reading_engine.job_store import ReadingConflict
from v2_reading_engine.read_models import (
    student_reading_status, supervisor_reading_results, supervisor_audio_binding,
)

router = APIRouter(prefix="/v2/reading", tags=["v2-reading"])


@router.get("/jobs/{job_id}")
def student_result(
    job_id: int,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """Only the child's own current reading, without grade/model internals."""
    try:
        return student_reading_status(db, job_id=job_id, student_id=student.id)
    except ReadingConflict as exc:
        raise HTTPException(status_code=404, detail="نتيجة القراءة غير متاحة") from exc


@router.get("/admin/results")
def staff_results(
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    state: str | None = Query(default=None, pattern="^(processing|completed|needs_attention)$"),
    _staff: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return supervisor_reading_results(db, limit=limit, offset=offset, state=state)


@router.get("/admin/jobs/{job_id}/audio")
def staff_recording(
    job_id: int,
    range_header: str | None = Header(default=None, alias="Range"),
    staff: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Existing protected audio streaming, not public S3 or a presigned URL."""
    try:
        key, _student_id = supervisor_audio_binding(db, job_id=job_id)
    except ReadingConflict as exc:
        raise HTTPException(status_code=404, detail="تسجيل القراءة غير متاح") from exc
    return recordings.play_by_key(key=key, range_header=range_header, researcher=staff)
