"""P08 replacement evidence: explicit supervisor request, learner submission, immutable history."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import storage
from db.learning_models import AssessmentQuestionResponse, LessonQuestionResponse, LessonSession, V2ReviewRetryTask
from db.models import AssessmentSession, AudioSubmission, AuditLog, Student, User
from dependencies import get_current_user, get_db
from v2_assessment_runtime import _session_release
from v2_content.projection import student_question
from v2_interaction_runtime import AnswerRequest, _canonical_answer
from v2_lesson_runtime import _require_preview_student
from v2_retry_state import active_retry
from v2_review_claims import enforce_review_claim, clear_review_claim

router = APIRouter(prefix="/v2/retries", tags=["v2-retries"])


class RetryRequest(BaseModel):
    reason: str = Field(min_length=10, max_length=2000)


def _owner(db: Session, kind: Literal["lesson", "assessment"], response_id: int, *, lock: bool = False):
    if kind == "lesson":
        query = db.query(LessonQuestionResponse).filter(LessonQuestionResponse.id == response_id)
    else:
        query = db.query(AssessmentQuestionResponse).filter(AssessmentQuestionResponse.id == response_id)
    row = (query.with_for_update() if lock else query).one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="الإجابة غير موجودة")
    if kind == "lesson":
        session = db.query(LessonSession).filter(LessonSession.id == row.lesson_session_id).one()
        release = _session_release(db, session)
        question = next((q for q in release["questions"] if q["id"] == row.question_id), None)
    else:
        session = db.query(AssessmentSession).filter(AssessmentSession.id == row.assessment_session_id).one()
        release = _session_release(db, session)
        question = next((q for q in release["questions"] if q["id"] == row.question_id), None)
    if not question or question["interaction"] not in ("read_aloud", "write_text"):
        raise HTTPException(status_code=409, detail="السؤال لا يقبل إعادة تسجيل أو كتابة")
    return row, session, question


@router.post("/admin/{kind}/{response_id}/request")
def request_retry(
    kind: Literal["lesson", "assessment"], response_id: int, body: RetryRequest,
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    row, session, question = _owner(db, kind, response_id, lock=True)
    if row.status != "pending_review":
        raise HTTPException(status_code=409, detail="لا يمكن طلب إعادة دليل مُقيَّم")
    enforce_review_claim(db, kind, row.id, user.id)
    task = active_retry(db, **{f"{kind}_response_id": row.id})
    if task:
        if task.status == "requested":
            raise HTTPException(status_code=409, detail="المهمة مطلوبة بالفعل؛ انتظر الطالب")
        task.status = "superseded"
        task.resolved_at = datetime.now(timezone.utc)
        db.flush()  # Free the partial unique active-task index before inserting the next request.
    if kind == "assessment" and session.v2_state not in ("waiting_review",):
        raise HTTPException(status_code=409, detail="إعادة التقييم لا تتاح قبل إكمال أسئلة الاختبار")
    if kind == "lesson" and session.status not in ("in_progress", "waiting_review") and not (
        session.status == "completed" and row.role == "guided_practice"
    ):
        raise HTTPException(status_code=409, detail="جلسة الدرس غير نشطة ولا يمكن طلب دليل جديد")
    request_kind = "rerecord" if question["interaction"] == "read_aloud" else "rewrite"
    replacement = V2ReviewRetryTask(
        lesson_response_id=row.id if kind == "lesson" else None,
        assessment_response_id=row.id if kind == "assessment" else None,
        student_id=session.student_id, requested_by=user.id,
        request_kind=request_kind, status="requested", reason=body.reason,
    )
    if request_kind == "rerecord":
        audios = db.query(AudioSubmission)
        audios = audios.filter(
            AudioSubmission.lesson_response_id == row.id if kind == "lesson"
            else AudioSubmission.assessment_response_id == row.id
        ).order_by(AudioSubmission.id.desc())
        old_audio = audios.first()
        if old_audio and old_audio.status == "pending_review":
            old_audio.status = "rerecord_required"
    db.add(replacement)
    db.flush()
    clear_review_claim(db, kind, row.id)
    db.add(AuditLog(
        actor_role="researcher", actor_id=user.id, action="v2_open_evidence_retry_requested",
        entity_type="v2_review_retry_task", entity_id=str(replacement.id),
        details=f"{kind}:{row.id}; {request_kind}; reason_location=v2_review_retry_tasks" ,
    ))
    db.commit()
    return {"status": "requested", "task_id": replacement.id, "request_kind": request_kind}


@router.get("/student/tasks")
def student_tasks(
    limit: int = Query(default=50, ge=1, le=100),
    student: Student = Depends(_require_preview_student), db: Session = Depends(get_db),
):
    rows = db.query(V2ReviewRetryTask).filter(
        V2ReviewRetryTask.student_id == student.id,
        V2ReviewRetryTask.status.in_(("requested", "submitted")),
    ).order_by(V2ReviewRetryTask.id.desc()).limit(limit).all()
    items = []
    for task in rows:
        kind = "lesson" if task.lesson_response_id is not None else "assessment"
        row, session, question = _owner(db, kind, task.lesson_response_id or task.assessment_response_id)
        staged = task.replacement_json if task.status == "requested" else None
        items.append({
            "staged_audio": staged.get("staged_audio") if isinstance(staged, dict) else None,
            "task_id": task.id, "kind": kind,
            "session_id": session.id, "question_id": row.question_id,
            "status": task.status, "request_kind": task.request_kind,
            "reason": task.reason, "prompt": student_question(question)["prompt"],
        })
    return {"items": items}


def _student_task(db: Session, task_id: int, student: Student, *, lock: bool = False):
    query = db.query(V2ReviewRetryTask).filter(
        V2ReviewRetryTask.id == task_id, V2ReviewRetryTask.student_id == student.id,
    )
    initial = query.one_or_none()
    if not initial:
        raise HTTPException(status_code=404, detail="مهمة الإعادة غير موجودة")
    kind = "lesson" if initial.lesson_response_id is not None else "assessment"
    # Consistent lock order: response first, retry task second, as in supervisor requests.
    row, session, question = _owner(db, kind, initial.lesson_response_id or initial.assessment_response_id, lock=lock)
    task = (query.with_for_update() if lock else query).one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="مهمة الإعادة غير موجودة")
    if row.status != "pending_review" or session.student_id != student.id:
        raise HTTPException(status_code=409, detail="المهمة غير متاحة لهذا الطالب")
    current = active_retry(db, **{f"{kind}_response_id": row.id})
    if not current or current.id != task.id:
        raise HTTPException(status_code=409, detail="مهمة الإعادة استبدلت بطلب أحدث")
    if kind == "lesson" and session.status not in ("in_progress", "waiting_review") and not (
        session.status == "completed" and row.role == "guided_practice"
    ):
        raise HTTPException(status_code=409, detail="جلسة الدرس منتهية")
    if kind == "assessment" and session.v2_state != "waiting_review":
        raise HTTPException(status_code=409, detail="جلسة الاختبار غير متاحة للإعادة")
    return task, kind, row, question


@router.post("/student/tasks/{task_id}/recording")
def student_retry_recording(
    task_id: int, file: UploadFile = File(...),
    duration_seconds: int | None = Form(default=None, ge=1, le=600),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=8, max_length=100),
    student: Student = Depends(_require_preview_student), db: Session = Depends(get_db),
):
    task, kind, row, question = _student_task(db, task_id, student)
    if task.status != "requested" or task.request_kind != "rerecord" or question["interaction"] != "read_aloud":
        raise HTTPException(status_code=409, detail="هذه المهمة لا تقبل ملف قراءة")
    accepted_formats = {"audio/webm", "audio/mp4", "audio/ogg", "audio/mpeg", "audio/wav", "audio/x-wav"}
    if (not file.content_type or file.content_type.split(";", 1)[0].strip().lower() not in accepted_formats):
        raise HTTPException(status_code=400, detail="صيغة التسجيل غير مدعومة")
    try:
        key, size, _ = storage.upload_audio(
            file, student.id, f"v2-retry:{task.id}:{idempotency_key}",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="ملف القراءة غير صالح") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="تعذر رفع التسجيل الآن") from exc
    metadata = {
        "audio_storage_key": key,
        "audio_file_size": size,
        "audio_mime_type": file.content_type,
        "audio_duration_seconds": duration_seconds,
    }
    # The request may have been finalized during an S3 upload. Recheck the
    # locked response before recording resumable upload metadata.
    current, _, _, _ = _student_task(db, task_id, student, lock=True)
    if current.status != "requested":
        raise HTTPException(status_code=409, detail="انتهى طلب إعادة التسجيل قبل اكتمال الرفع")
    previous = current.replacement_json if isinstance(current.replacement_json, dict) else {}
    old_staged = previous.get("staged_audio")
    superseded = list(previous.get("superseded_staged_audio") or [])
    # When the child explicitly records again, retain prior private object keys
    # for controlled retention; never delete or orphan earlier uploads silently.
    if old_staged and old_staged != metadata:
        superseded.append(old_staged)
    current.replacement_json = {
        "staged_audio": metadata,
        "superseded_staged_audio": superseded,
    }
    db.commit()
    return metadata


@router.post("/student/tasks/{task_id}/submit")
def student_retry_submit(
    task_id: int, body: AnswerRequest,
    student: Student = Depends(_require_preview_student), db: Session = Depends(get_db),
):
    task, kind, row, question = _student_task(db, task_id, student, lock=True)
    if task.status == "submitted":
        previous = task.replacement_json or {}
        if task.submit_key != body.submit_key:
            raise HTTPException(status_code=409, detail="أُرسلت المهمة بالفعل ولا تقبل التكرار")
        if task.request_kind == "rewrite":
            same = (body.text_response or "").strip() == previous.get("text_response")
        else:
            same = (
                body.audio_storage_key == previous.get("audio_storage_key")
                and body.audio_file_size == previous.get("audio_file_size")
                and body.audio_mime_type == previous.get("audio_mime_type")
                and body.audio_duration_seconds == previous.get("audio_duration_seconds")
            )
        if not same:
            raise HTTPException(status_code=409, detail="مفتاح الإرسال سبق استخدامه لدليل مختلف")
        return {"status": "replayed", "task_id": task.id}
    if task.status != "requested":
        raise HTTPException(status_code=409, detail="مهمة الإعادة ليست مفتوحة")
    canonical = _canonical_answer(question, body, student.id)
    if (question["interaction"] == "read_aloud") != (task.request_kind == "rerecord"):
        raise HTTPException(status_code=409, detail="نوع الدليل لا يطابق طلب الإعادة")
    if task.request_kind == "rerecord":
        staged = (task.replacement_json or {}).get("staged_audio")
        if staged:
            fields = ("audio_storage_key", "audio_file_size", "audio_mime_type", "audio_duration_seconds")
            if any(staged.get(field) != canonical.get(field) for field in fields):
                raise HTTPException(status_code=409, detail="ملف الإعادة المرسل لا يطابق التسجيل المرفوع للمهمة")
    if task.request_kind == "rerecord":
        # Preserve private keys of replaced, never-submitted uploads for later
        # retention management. Reviewers still grade only the current audio.
        old_staging = task.replacement_json if isinstance(task.replacement_json, dict) else {}
        superseded = old_staging.get("superseded_staged_audio") or []
        if superseded:
            canonical["superseded_staged_audio"] = superseded
    task.replacement_json = canonical
    task.submit_key = body.submit_key
    task.submitted_at = datetime.now(timezone.utc)
    task.status = "submitted"
    if task.request_kind == "rerecord":
        audio = AudioSubmission(
            response_id=None,
            lesson_response_id=row.id if kind == "lesson" else None,
            assessment_response_id=row.id if kind == "assessment" else None,
            storage_key=canonical["audio_storage_key"],
            file_size=canonical["audio_file_size"],
            mime_type=canonical["audio_mime_type"],
            duration_seconds=canonical["audio_duration_seconds"], status="pending_review",
        )
        db.add(audio)
        db.flush()
        task.audio_submission_id = audio.id
    db.add(AuditLog(
        actor_role="student", actor_id=student.id, action="v2_open_evidence_retry_submitted",
        entity_type="v2_review_retry_task", entity_id=str(task.id),
        details=f"{kind}:{row.id}; {task.request_kind}",
    ))
    db.commit()
    return {"status": "submitted", "task_id": task.id, "awaiting_human_review": True}
