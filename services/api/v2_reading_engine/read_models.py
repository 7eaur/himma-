"""Native V2 reading projections: no Azure metadata in student responses.

Only jobs explicitly owned by the authenticated student may be projected.
The administrative view is read-only and never grants or changes grades.
"""
from __future__ import annotations

from decimal import Decimal
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from db.models import Student, AudioSubmission
from db.learning_models import LessonQuestionResponse
from db.v2_reading_models import V2ReadingJob, V2ReadingEvaluation
from .job_store import ReadingConflict


PROCESSING = "نستمع إلى قراءتك..."
RETRY = "ما فهمت قراءتك بوضوح. جرّب التسجيل مرة ثانية."
SERVICE = "تعذر التحقق الآن. تسجيلك محفوظ؛ حاول المتابعة بعد قليل."
DONE = "تم تسجيل قراءتك. نكمل السؤال التالي."
GOOD = "أحسنت! قراءتك صحيحة، هيا نكمل."
TRY_AGAIN = "اقتربت! اقرأ المطلوب وحاول مرة ثانية."


def _current_job(db: Session, job_id: int, *, student_id: int | None = None) -> V2ReadingJob:
    query = select(V2ReadingJob).where(
        V2ReadingJob.id == job_id,
        V2ReadingJob.is_current.is_(True),
    )
    if student_id is not None:
        query = query.where(V2ReadingJob.student_id == student_id)
    job = db.scalar(query)
    if job is None:
        raise ReadingConflict("Reading job not found")
    return job


def student_reading_status(db: Session, *, job_id: int, student_id: int) -> dict:
    job = _current_job(db, job_id, student_id=student_id)
    result = None
    if job.status == "applied":
        result = db.scalar(select(V2ReadingEvaluation).where(
            V2ReadingEvaluation.job_id == job.id
        ))
        if result is None:
            raise ReadingConflict("Applied reading grade has no evidence")

    if job.status == "retry_audio":
        return {"state": "retry_audio", "message": RETRY, "retry_required": True}
    if job.status == "service_unavailable":
        return {"state": "unavailable", "message": SERVICE, "retry_required": False}
    if result is not None:
        if job.learning_mode == "assessment":
            return {"state": "completed", "message": DONE, "retry_required": False}
        if result.passed_for_progress:
            return {"state": "correct", "message": GOOD, "retry_required": False}
        hint = result.evidence_json.get("training_hint")
        # A graded training mistake is not an unrecognized recording.
        output = {
            "state": "incorrect", "message": TRY_AGAIN,
            "hint": hint if isinstance(hint, str) and 0 < len(hint) <= 250 else TRY_AGAIN,
            "retry_required": False,
        }
        # Only the final incorrect attempt of a FOCUSED SUPPORT practice
        # may reveal the existing reference as a worked reading model.
        # Never expose this in pre/posttests, unaided support checks or ordinary
        # guided lessons, even if the browser asks for a different job ID.
        if job.lesson_response_id is not None:
            answer = db.get(LessonQuestionResponse, job.lesson_response_id)
            if (answer is not None and answer.role == "guided_practice"
                    and answer.support_assignment_id is not None
                    and answer.attempt_no >= 3 and answer.is_correct is False
                    and answer.status == "graded"):
                output.update({
                    "assisted_advance": True,
                    "model_text": job.reference_text,
                    "message": "اقرأ المثال، ثم نتابع خطوة جديدة.",
                })
        return output
    return {"state": "processing", "message": PROCESSING, "retry_required": False}


def supervisor_reading_results(
    db: Session, *, limit: int = 30, offset: int = 0,
    state: str | None = None,
    search: str | None = None,
) -> dict:
    if not 1 <= limit <= 100 or offset < 0:
        raise ValueError("Invalid pagination")
    state_aliases = {
        "processing": {"queued", "processing", "retry_wait", "evidence_ready"},
        "completed": {"applied"},
        "needs_attention": {"retry_audio", "service_unavailable"},
    }
    if state is not None and state not in state_aliases:
        raise ValueError("Invalid reading state")
    where = [V2ReadingJob.is_current.is_(True)]
    if state is not None:
        where.append(V2ReadingJob.status.in_(state_aliases[state]))
    if search:
        term = search.strip()
        if len(term) > 80:
            raise ValueError("Reading search exceeds 80 characters")
        if term:
            escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            pattern = f"%{escaped}%"
            where.append(or_(
                Student.name.ilike(pattern, escape="\\"),
                V2ReadingJob.question_id.ilike(pattern, escape="\\"),
            ))

    count = db.scalar(
        select(func.count(V2ReadingJob.id))
        .select_from(V2ReadingJob)
        .join(Student, Student.id == V2ReadingJob.student_id)
        .where(*where)
    ) or 0
    rows = db.execute(
        select(V2ReadingJob, Student, V2ReadingEvaluation, AudioSubmission)
        .join(Student, Student.id == V2ReadingJob.student_id)
        .outerjoin(V2ReadingEvaluation, V2ReadingEvaluation.job_id == V2ReadingJob.id)
        .outerjoin(AudioSubmission, AudioSubmission.id == V2ReadingJob.audio_submission_id)
        .where(*where)
        .order_by(V2ReadingJob.created_at.desc(), V2ReadingJob.id.desc())
        .offset(offset).limit(limit)
    ).all()
    output = []
    for job, student, evaluation, audio in rows:
        if job.status == "applied":
            label = "صحيحة" if evaluation and evaluation.passed_for_progress else "تحتاج تقوية"
        elif job.status == "retry_audio":
            label = "إعادة تسجيل مطلوبة"
        elif job.status == "service_unavailable":
            label = "تعذر التحليل مؤقتًا"
        else:
            label = "جاري التحقق"
        output.append({
            "job_id": job.id,
            "student_id": student.id,
            "student_name": student.name,
            "question_id": job.question_id,
            "reference": job.reference_text,
            "kind": job.reading_kind,
            "session_kind": "assessment" if job.assessment_response_id else "lesson",
            "result": label,
            "score_percent": round(float(evaluation.score_fraction) * 100, 3)
            if job.status == "applied" and evaluation and job.reading_kind in {"sentence", "text"}
            else None,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "has_audio": _audio_available(job, audio),
        })
    return {
        "items": output,
        "total": count,
        "next_offset": offset + limit if offset + limit < count else None,
    }


def _audio_available(job: V2ReadingJob, audio: AudioSubmission | None) -> bool:
    """Do not offer a player for a deleted, superseded or mismatched take."""
    return bool(
        audio is not None
        and audio.status not in {"purged", "retention_pending"}
        and audio.file_size > 0
        and audio.storage_key.startswith(f"audio/{job.student_id}/")
        and (job.assessment_response_id is None
             or audio.assessment_response_id == job.assessment_response_id)
        and (job.lesson_response_id is None
             or audio.lesson_response_id == job.lesson_response_id)
    )


def supervisor_audio_binding(db: Session, *, job_id: int) -> tuple[str, int]:
    job = _current_job(db, job_id)
    audio = db.get(AudioSubmission, job.audio_submission_id)
    if not _audio_available(job, audio):
        raise ReadingConflict("Private reading recording does not match job")
    return audio.storage_key, job.student_id
