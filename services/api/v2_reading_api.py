"""Student-safe speech progress and supervisor-only reading results.

This replaces manual-review display contracts in the V2 rebuild branch.
No API route grants a grade, exposes raw ASR, or mutates student audio.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

import recordings
import storage
import uuid
from sqlalchemy import select
from db.models import AudioSubmission, AudioUploadLease
from db.v2_reading_models import V2ReadingJob
from v2_audio_retention import audio_upload_binding, track_new_audio_upload
from v2_reading_engine.re_recording import attach_retry_take, retry_is_allowed
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
    search: str | None = Query(default=None, max_length=80),
    _staff: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return supervisor_reading_results(db, limit=limit, offset=offset, state=state, search=search)


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


@router.post("/jobs/{job_id}/rerecord")
def rerecord_unclear_reading(
    job_id: int,
    file: UploadFile = File(...),
    duration_seconds: float = Form(..., gt=0, le=900),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=8, max_length=100,
                                  pattern=r"^[A-Za-z0-9._:-]+$"),
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """Provider could not recognize audio: replace its take without a new attempt.

    No provider call or grading occurs in the request, and the student only
    receives a new polling ID, not Azure/error/alias internals. Upload leases
    are staged first so a failed DB claim can be cleaned by normal retention.
    """
    allowed = {"audio/wav", "audio/webm", "audio/mp4", "audio/ogg", "audio/mpeg"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="صيغة التسجيل غير مدعومة. أعد التسجيل.")
    operation = f"v2-reading-retry:{job_id}:{idempotency_key}"
    deterministic_id = uuid.uuid5(
        uuid.NAMESPACE_URL, f"himma-audio:{student.id}:{operation}"
    )
    possible_keys = (
        f"audio/{student.id}/{deterministic_id}.audio",
        f"audio/{student.id}/{deterministic_id}.webm",
    )
    try:
        source_job = retry_is_allowed(db, student_id=student.id, job_id=job_id)
    except ReadingConflict as exc:
        # A repeated *identical* upload after a successful response must
        # remain idempotent. Do not allow an arbitrary new retry operation.
        original = db.scalar(select(V2ReadingJob).where(
            V2ReadingJob.id == job_id, V2ReadingJob.student_id == student.id,
        ))
        if original is None:
            raise HTTPException(status_code=404, detail="التسجيل غير متاح") from exc
        source_job = original
        candidate = db.scalar(select(AudioSubmission).where(
            AudioSubmission.storage_key.in_(possible_keys),
            AudioSubmission.assessment_response_id == original.assessment_response_id
            if original.assessment_response_id is not None
            else AudioSubmission.lesson_response_id == original.lesson_response_id,
        ))
        if candidate is None:
            raise HTTPException(status_code=409, detail="لا توجد إعادة تسجيل مطلوبة لهذا السؤال") from exc
        lease = db.scalar(select(AudioUploadLease).where(
            AudioUploadLease.storage_key == candidate.storage_key,
            AudioUploadLease.student_id == student.id,
            AudioUploadLease.binding_key == audio_upload_binding(
                "retry", original.id, original.question_id),
            AudioUploadLease.state == "submitted",
        ))
        if lease is None:
            raise HTTPException(status_code=409, detail="هذا التسجيل لم يعد متاحًا للإرسال") from exc
    else:
        # The owner/status lock was verified before touching private storage.
        db.rollback()
    try:
        key, size, _ = storage.upload_audio(file, student.id, operation)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="تعذر حفظ هذا التسجيل. أعد التسجيل.") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="تعذر حفظ التسجيل حاليًا. حاول مرة أخرى.") from exc

    try:
        db.rollback()
        track_new_audio_upload(
            db, student_id=student.id, storage_key=key,
            binding_key=audio_upload_binding("retry", job_id, source_job.question_id),
        )
        db.commit()  # Keep abandoned audio discoverable if the next step fails.
        new_job = attach_retry_take(
            db, student_id=student.id, job_id=job_id,
            storage_key=key, file_size=size, mime_type=file.content_type,
            duration_seconds=duration_seconds,
        )
        db.commit()
    except (ReadingConflict, ValueError) as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="تعذر استبدال التسجيل. حدّث السؤال وحاول مرة أخرى.") from exc
    return {"job_id": new_job.id, "state": "processing",
            "message": "وصل تسجيلك الجديد. نستمع إلى قراءتك..."}
