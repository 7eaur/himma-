"""P08 learner-evidence supervisor review: private, serialized and auditable.

This first increment resolves lesson answers without fabricating automatic
pronunciation grades. Historical evidence remains immutable, and the student's
mastery projection changes only after the authenticated supervisor's decision.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import recordings
import storage
from db.learning_models import (
    AdaptationDecision, LessonQuestionResponse, LessonSession,
    SkillEvidence, V2LessonReviewAction,
)
from db.models import AudioSubmission, AuditLog, Student, User
from dependencies import get_current_user, get_db
from v2_adaptation_runtime import (
    active_support_assignment, finish_independent_check,
    finish_support_check,
)
from v2_content.repository import get_release
from v2_assessment_runtime import _session_release
from v2_retry_state import active_retry

router = APIRouter(prefix="/v2/review", tags=["v2-review"])


class LessonDecision(BaseModel):
    is_correct: bool
    note: str = Field(min_length=2, max_length=2000)


def _lesson_audio(db: Session, response_id: int) -> AudioSubmission | None:
    task = active_retry(db, lesson_response_id=response_id)
    if task:
        if task.status != "submitted" or not task.audio_submission_id:
            return None
        return db.query(AudioSubmission).filter(
            AudioSubmission.id == task.audio_submission_id,
            AudioSubmission.lesson_response_id == response_id,
        ).one_or_none()
    return db.query(AudioSubmission).filter(
        AudioSubmission.lesson_response_id == response_id
    ).order_by(AudioSubmission.id.desc()).first()


def _question(db: Session, row: LessonQuestionResponse, session: LessonSession) -> dict:
    # An older learner's human reading rubric must never be silently replaced by
    # a newer release's rubric. The shared assessment resolver is checksum-pinned.
    release = _session_release(db, session)
    question = next((q for q in release["questions"] if q["id"] == row.question_id), None)
    if not question or question["role"] != row.role or question["interaction"] not in {"read_aloud", "write_text"}:
        raise HTTPException(status_code=409, detail="دليل الدرس لا يطابق نسخته الأصلية")
    return question


def _item(db: Session, row: LessonQuestionResponse, session: LessonSession, student: Student) -> dict:
    question = _question(db, row, session)
    task = active_retry(db, lesson_response_id=row.id)
    audio = _lesson_audio(db, row.id) if question["interaction"] == "read_aloud" else None
    answer = (task.replacement_json if task and task.status == "submitted" else
              (row.answer_json or {}).get("answer")) or {}
    ready = (
        bool(audio and audio.status == "pending_review" and audio.file_size > 0
             and audio.storage_key.startswith(f"audio/{session.student_id}/"))
        if audio is not None or question["interaction"] == "read_aloud"
        else bool(str(answer.get("text_response") or "").strip())
    )
    if task and task.status == "requested":
        ready = False
    return {
        "retry_state": task.status if task else None,
        "response_id": row.id, "session_id": session.id,
        "student_id": student.id, "student_name": student.name,
        "question_id": row.question_id, "lesson_id": session.lesson_id,
        "interaction": question["interaction"], "prompt": question["prompt"],
        "reference": question.get("reading_reference") if question["interaction"] == "read_aloud" else None,
        "rubric": (question.get("private_answer") or {}).get("rubric"),
        "text_response": answer.get("text_response") if question["interaction"] == "write_text" else None,
        "audio_url": f"/api/v2/review/lessons/{row.id}/audio" if audio and ready else None,
        "evidence_ready": ready,
        "submitted_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("/lesson-queue")
def lesson_queue(
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.query(LessonQuestionResponse, LessonSession, Student).join(
        LessonSession, LessonSession.id == LessonQuestionResponse.lesson_session_id
    ).join(Student, Student.id == LessonSession.student_id).filter(
        LessonQuestionResponse.status == "pending_review",
    ).order_by(LessonQuestionResponse.created_at, LessonQuestionResponse.id).offset(offset).limit(limit + 1).all()
    return {"items": [_item(db, row, session, student) for row, session, student in rows[:limit]],
            "next_offset": offset + limit if len(rows) > limit else None}


@router.get("/lessons/{response_id}/audio")
def lesson_audio(
    response_id: int,
    range_header: str | None = Header(default=None, alias="Range"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.query(LessonQuestionResponse).filter(LessonQuestionResponse.id == response_id).one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="لا يوجد تسجيل لهذه الإجابة")
    session = db.query(LessonSession).filter(LessonSession.id == row.lesson_session_id).one()
    if _question(db, row, session)["interaction"] != "read_aloud":
        raise HTTPException(status_code=404, detail="لا يوجد تسجيل لهذا السؤال")
    audio = _lesson_audio(db, row.id)
    if not audio or not audio.storage_key.startswith(f"audio/{session.student_id}/"):
        raise HTTPException(status_code=404, detail="تسجيل الطالب غير متاح")
    return recordings.play_by_key(key=audio.storage_key, range_header=range_header, researcher=user)


@router.post("/lessons/{response_id}/decision")
def decide_lesson(
    response_id: int,
    body: LessonDecision,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.query(LessonQuestionResponse).filter(
        LessonQuestionResponse.id == response_id
    ).with_for_update().one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="إجابة الدرس غير موجودة")
    if row.status != "pending_review":
        raise HTTPException(status_code=409, detail="تمت مراجعة الإجابة؛ لا يقبل القرار المكرر")
    session = db.query(LessonSession).filter(LessonSession.id == row.lesson_session_id).with_for_update().one()
    student = db.query(Student).filter(Student.id == session.student_id).one()
    evidence = _item(db, row, session, student)
    if not evidence["evidence_ready"]:
        raise HTTPException(status_code=409, detail="لا يوجد دليل صالح لتقييم الإجابة")
    audio = _lesson_audio(db, row.id) if evidence["interaction"] == "read_aloud" else None
    if audio:
        try:
            storage.verify_audio(audio.storage_key, audio.file_size, audio.mime_type)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail="ملف القراءة مفقود أو تغير") from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail="تعذر التحقق من الملف الصوتي الآن") from exc

    now = datetime.now(timezone.utc)
    row.status = "graded"
    row.is_correct = body.is_correct
    row.reviewed_at = now
    if audio:
        audio.status = "graded"
    proof = db.query(SkillEvidence).filter(SkillEvidence.response_id == row.id).with_for_update().one_or_none()
    if not proof:
        raise HTTPException(status_code=409, detail="دليل المهارة المرتبط بالإجابة غير موجود")
    task = active_retry(db, lesson_response_id=row.id)
    if task and task.status == "requested":
        raise HTTPException(status_code=409, detail="المشرف طلب إعادة الدليل؛ انتظر النسخة الجديدة")
    if task and task.status == "submitted":
        task.status = "resolved"
        task.resolved_at = now
    proof.review_status = "graded"
    proof.is_correct = body.is_correct
    proof.reviewed_at = now
    proof.counts_for_mastery = row.role in {"independent_check", "support_check"}
    db.add(V2LessonReviewAction(
        lesson_response_id=row.id, reviewer_id=user.id, action="graded",
        is_correct=body.is_correct, note=body.note, created_at=now,
    ))
    db.add(AuditLog(
        actor_role="researcher", actor_id=user.id, action="v2_lesson_response_reviewed",
        entity_type="lesson_question_response", entity_id=str(row.id),
        details=f"decision={body.is_correct}; note={body.note}",
    ))
    db.flush()
    remaining = db.query(LessonQuestionResponse).filter(
        LessonQuestionResponse.lesson_session_id == session.id,
        LessonQuestionResponse.status == "pending_review",
    ).count()
    if not remaining and session.stage == "waiting_review" and session.status == "waiting_review":
        # P05 progression is still compiled from the live bank; do not mutate
        # an immutable old session using different support/lesson definitions.
        from db.models import ContentRelease
        pinned = db.query(ContentRelease).filter(ContentRelease.id == session.content_release_id).one()
        compiled = get_release()
        if pinned.checksum != compiled["checksum"] or pinned.version != compiled["version"]:
            raise HTTPException(status_code=409, detail="قرار التكيف يتطلب إصدار الدرس المحفوظ")
        decision = db.query(AdaptationDecision).filter(
            AdaptationDecision.lesson_session_id == session.id
        ).order_by(AdaptationDecision.id.desc()).first()
        if not decision or decision.decision_kind != "waiting_review":
            raise HTTPException(status_code=409, detail="حالة تعليق الدرس لا تطابق قرار التكيف")
        if decision.support_assignment_id is None:
            finish_independent_check(db, session, decision_key=f"independent:reviewed:{row.id}")
        else:
            assignment = active_support_assignment(db, session.id)
            if not assignment or assignment.id != decision.support_assignment_id:
                raise HTTPException(status_code=409, detail="إسناد الدعم المعلق لا يطابق الأدلة")
            finish_support_check(db, session, assignment, decision_key=f"support:{assignment.id}:reviewed:{row.id}")
    db.commit()
    return {"status": "graded", "lesson_stage": session.stage, "session_status": session.status,
            "pending_review": remaining}
