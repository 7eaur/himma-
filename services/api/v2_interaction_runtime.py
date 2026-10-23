"""P04 unified interaction runtime for the V2 lesson session.

All seven interactions consume the immutable authoring bank. Correct answers
and review rubrics stay server-side; the learner receives only role-appropriate
feedback. Open writing and reading remain academically pending until a human
supervisor reviews them.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

import storage
from db.learning_models import LessonQuestionDraft, LessonQuestionResponse, LessonSession
from db.models import AudioSubmission, Student
from dependencies import get_db
from v2_content.media import MediaProvider
from v2_content.projection import student_question
from v2_content.repository import get_lesson, get_media, get_question
from v2_lesson_runtime import _require_preview_student, _session_or_404, _session_payload


router = APIRouter(prefix="/v2/lessons", tags=["v2-interactions"])
CHOICE_INTERACTIONS = {"choose_one", "listen_choose_one", "choose_image"}
ORDER_INTERACTIONS = {"sequence", "build_word"}
OPEN_INTERACTIONS = {"read_aloud", "write_text"}
STAGE_ROLE = {
    "guided_practice": "guided_practice",
    "independent_check": "independent_check",
}


class AnswerRequest(BaseModel):
    submit_key: str = Field(min_length=8, max_length=100, pattern=r"^[A-Za-z0-9._:-]+$")
    selected_option_ids: list[str] | None = None
    text_response: str | None = Field(default=None, max_length=500)
    audio_storage_key: str | None = Field(default=None, max_length=255)
    audio_file_size: int | None = Field(default=None, gt=0, le=storage.MAX_AUDIO_BYTES)
    audio_mime_type: str | None = Field(default=None, max_length=100)
    audio_duration_seconds: float | None = Field(default=None, gt=0, le=900)

    @model_validator(mode="after")
    def one_answer_shape(self):
        shapes = sum(
            value is not None
            for value in (self.selected_option_ids, self.text_response, self.audio_storage_key)
        )
        if shapes != 1:
            raise ValueError("أرسل إجابة واحدة فقط")
        return self


class DraftRequest(BaseModel):
    text: str = Field(max_length=500)


def _question_ids(session: LessonSession) -> list[str]:
    lesson = get_lesson(session.lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="الدرس غير موجود")
    if session.stage == "guided_practice":
        return list(lesson["practice_question_ids"])
    if session.stage == "independent_check":
        return list(lesson["check_question_ids"])
    return []


def _current_question(session: LessonSession) -> dict[str, Any]:
    question_ids = _question_ids(session)
    if not question_ids:
        raise HTTPException(status_code=409, detail="لا يوجد سؤال متاح في مرحلة الدرس الحالية")
    if session.step_index >= len(question_ids):
        raise HTTPException(status_code=409, detail="موضع السؤال المحفوظ غير صالح")
    question = get_question(question_ids[session.step_index])
    if not question:
        raise HTTPException(status_code=409, detail="سؤال الدرس غير مسجل في الإصدار")
    expected_role = STAGE_ROLE.get(session.stage)
    if question["role"] != expected_role:
        raise HTTPException(status_code=409, detail="عقد سؤال الدرس لا يطابق مرحلته")
    return question


def _resolved_media(question: dict[str, Any]) -> dict[str, dict[str, Any]]:
    media_ids: set[str] = set()
    for item in question.get("stimulus", {}).get("media", []):
        media_ids.add(item["media_id"])
    for option in question.get("options", []):
        for item in option.get("media", []):
            media_ids.add(item["media_id"])
    provider = MediaProvider()
    result = {}
    for media_id in sorted(media_ids):
        asset = get_media(media_id)
        if not asset:
            raise HTTPException(status_code=409, detail="أحد أصول السؤال غير مسجل")
        result[media_id] = provider.resolve(asset).as_dict()
    return result


def _draft(db: Session, session_id: int, question_id: str) -> LessonQuestionDraft | None:
    return db.query(LessonQuestionDraft).filter(
        LessonQuestionDraft.lesson_session_id == session_id,
        LessonQuestionDraft.question_id == question_id,
    ).one_or_none()


def _interaction_payload(db: Session, session: LessonSession) -> dict[str, Any]:
    base = _session_payload(session)
    if session.stage not in STAGE_ROLE:
        base["interaction"] = None
        base["summary"] = {
            "submitted": db.query(LessonQuestionResponse).filter(
                LessonQuestionResponse.lesson_session_id == session.id,
            ).count(),
            "pending_review": db.query(LessonQuestionResponse).filter(
                LessonQuestionResponse.lesson_session_id == session.id,
                LessonQuestionResponse.status == "pending_review",
            ).count(),
        }
        return base

    question = _current_question(session)
    question_ids = _question_ids(session)
    projected = student_question(question)
    saved_draft = _draft(db, session.id, question["id"])
    base["interaction"] = {
        "question": projected,
        "media": _resolved_media(question),
        "progress": {
            "index": session.step_index + 1,
            "total": len(question_ids),
            "stage": session.stage,
        },
        "attempts": db.query(LessonQuestionResponse).filter(
            LessonQuestionResponse.lesson_session_id == session.id,
            LessonQuestionResponse.question_id == question["id"],
        ).count(),
        "draft": (saved_draft.draft_json or {}).get("text") if saved_draft else None,
    }
    return base


def _canonical_answer(question: dict[str, Any], body: AnswerRequest, student_id: int) -> dict[str, Any]:
    interaction = question["interaction"]
    option_ids = [option["id"] for option in question["options"]]
    if interaction in CHOICE_INTERACTIONS:
        selected = body.selected_option_ids or []
        if len(selected) != 1 or selected[0] not in option_ids:
            raise HTTPException(status_code=422, detail="اختر خيارًا واحدًا صالحًا")
        return {"selected_option_ids": selected}
    if interaction in ORDER_INTERACTIONS:
        selected = body.selected_option_ids or []
        if len(selected) != len(option_ids) or len(set(selected)) != len(selected) or set(selected) != set(option_ids):
            raise HTTPException(status_code=422, detail="رتب جميع العناصر مرة واحدة")
        return {"selected_option_ids": selected}
    if interaction == "write_text":
        text = (body.text_response or "").strip()
        if not text:
            raise HTTPException(status_code=422, detail="اكتب إجابتك قبل الحفظ")
        return {"text_response": text}
    if interaction == "read_aloud":
        if not all((body.audio_storage_key, body.audio_file_size, body.audio_mime_type, body.audio_duration_seconds)):
            raise HTTPException(status_code=422, detail="بيانات التسجيل غير مكتملة")
        if not body.audio_storage_key.startswith(f"audio/{student_id}/"):
            raise HTTPException(status_code=403, detail="التسجيل لا يخص هذا الطالب")
        try:
            storage.verify_audio(
                body.audio_storage_key,
                body.audio_file_size,
                expected_content_type=body.audio_mime_type,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="ملف التسجيل غير صالح") from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail="خدمة حفظ التسجيلات غير متاحة الآن") from exc
        return {
            "audio_storage_key": body.audio_storage_key,
            "audio_file_size": body.audio_file_size,
            "audio_mime_type": body.audio_mime_type,
            "audio_duration_seconds": body.audio_duration_seconds,
        }
    raise HTTPException(status_code=409, detail="نوع التفاعل غير مدعوم")


def _advance(session: LessonSession, question_count: int, *, has_pending: bool, db: Session) -> None:
    if session.step_index + 1 < question_count:
        session.step_index += 1
    elif session.stage == "guided_practice":
        session.stage = "independent_check"
        session.step_index = 0
    else:
        pending_count = db.query(LessonQuestionResponse).filter(
            LessonQuestionResponse.lesson_session_id == session.id,
            LessonQuestionResponse.status == "pending_review",
        ).count()
        session.stage = "waiting_review" if pending_count or has_pending else "complete"
        session.status = "waiting_review" if pending_count or has_pending else "completed"
        session.step_index = 0
        if session.status == "completed":
            session.completed_at = datetime.now(timezone.utc)
    session.version += 1
    session.updated_at = datetime.now(timezone.utc)


@router.get("/sessions/{session_id}/interaction")
def current_interaction(
    session_id: int,
    student: Student = Depends(_require_preview_student),
    db: Session = Depends(get_db),
):
    return _interaction_payload(db, _session_or_404(db, session_id, student.id))


@router.put("/sessions/{session_id}/draft")
def save_writing_draft(
    session_id: int,
    body: DraftRequest,
    student: Student = Depends(_require_preview_student),
    db: Session = Depends(get_db),
):
    session = _session_or_404(db, session_id, student.id)
    question = _current_question(session)
    if question["interaction"] != "write_text":
        raise HTTPException(status_code=409, detail="المسودة متاحة لسؤال الكتابة الحالي فقط")
    draft = _draft(db, session.id, question["id"])
    now = datetime.now(timezone.utc)
    if draft:
        draft.draft_json = {"text": body.text}
        draft.version += 1
        draft.updated_at = now
    else:
        draft = LessonQuestionDraft(
            lesson_session_id=session.id,
            question_id=question["id"],
            draft_json={"text": body.text},
            created_at=now,
            updated_at=now,
        )
        db.add(draft)
    db.commit()
    return {"status": "saved", "question_id": question["id"], "version": draft.version}


@router.post("/sessions/{session_id}/recording")
def upload_reading(
    session_id: int,
    file: UploadFile = File(...),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=8, max_length=100),
    student: Student = Depends(_require_preview_student),
    db: Session = Depends(get_db),
):
    session = _session_or_404(db, session_id, student.id)
    question = _current_question(session)
    if question["interaction"] != "read_aloud":
        raise HTTPException(status_code=409, detail="التسجيل متاح لسؤال القراءة الحالي فقط")
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="اختر تسجيلًا صوتيًا صالحًا")
    try:
        storage_key, file_size, _ = storage.upload_audio(
            file,
            student.id,
            f"v2:{session.id}:{question['id']}:{idempotency_key}",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="ملف التسجيل غير صالح") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="خدمة حفظ التسجيلات غير متاحة الآن") from exc
    return {
        "audio_storage_key": storage_key,
        "audio_file_size": file_size,
        "audio_mime_type": file.content_type,
    }


@router.post("/sessions/{session_id}/answers")
def submit_answer(
    session_id: int,
    body: AnswerRequest,
    student: Student = Depends(_require_preview_student),
    db: Session = Depends(get_db),
):
    session = db.query(LessonSession).filter(
        LessonSession.id == session_id,
        LessonSession.student_id == student.id,
    ).with_for_update().one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="جلسة الدرس غير موجودة")

    existing = db.query(LessonQuestionResponse).filter(
        LessonQuestionResponse.lesson_session_id == session.id,
        LessonQuestionResponse.submit_key == body.submit_key,
    ).one_or_none()
    if existing:
        submitted = existing.answer_json.get("answer") if isinstance(existing.answer_json, dict) else None
        candidate_question = get_question(existing.question_id)
        if not candidate_question:
            raise HTTPException(status_code=409, detail="السؤال السابق غير موجود في الإصدار")
        canonical = _canonical_answer(candidate_question, body, student.id)
        if submitted != canonical:
            raise HTTPException(status_code=409, detail="مفتاح الإرسال استُخدم لإجابة مختلفة")
        return {
            "status": "replayed",
            "submission": existing.answer_json.get("public_result", {}),
            "lesson": _interaction_payload(db, session),
        }

    if session.status != "in_progress" or session.stage not in STAGE_ROLE:
        raise HTTPException(status_code=409, detail="جلسة الدرس لا تقبل إجابات الآن")
    question = _current_question(session)
    canonical = _canonical_answer(question, body, student.id)
    attempts = db.query(LessonQuestionResponse).filter(
        LessonQuestionResponse.lesson_session_id == session.id,
        LessonQuestionResponse.question_id == question["id"],
    ).count()
    attempt_no = attempts + 1
    expected = question["private_answer"]["correct_option_ids"]
    is_open = question["interaction"] in OPEN_INTERACTIONS
    if is_open:
        is_correct = None
    elif question["interaction"] in ORDER_INTERACTIONS:
        is_correct = canonical["selected_option_ids"] == expected
    else:
        is_correct = set(canonical["selected_option_ids"]) == set(expected)

    guided = session.stage == "guided_practice"
    should_advance = is_open or not guided or bool(is_correct)
    public_result: dict[str, Any] = {
        "question_id": question["id"],
        "status": "pending_review" if is_open else "graded",
        "accepted": True,
        "retry_required": guided and is_correct is False,
    }
    if guided and is_correct is not None:
        public_result["correct"] = bool(is_correct)
        if not is_correct:
            public_result["hint"] = question.get("hint")
            public_result["message"] = "اقتربت! اقرأ التلميح ثم حاول مرة أخرى."
    elif is_open:
        public_result["message"] = "حُفظت إجابتك وتنتظر مراجعة المشرف."
    else:
        public_result["message"] = "تم حفظ إجابتك."

    response = LessonQuestionResponse(
        lesson_session_id=session.id,
        question_id=question["id"],
        role=question["role"],
        answer_json={"answer": canonical, "public_result": public_result},
        submit_key=body.submit_key,
        attempt_no=attempt_no,
        status="pending_review" if is_open else "graded",
        is_correct=is_correct,
        hint_used=guided and is_correct is False,
    )
    db.add(response)
    db.flush()
    if question["interaction"] == "read_aloud":
        db.add(AudioSubmission(
            response_id=None,
            lesson_response_id=response.id,
            storage_key=canonical["audio_storage_key"],
            file_size=canonical["audio_file_size"],
            mime_type=canonical["audio_mime_type"],
            duration_seconds=canonical["audio_duration_seconds"],
            status="pending_review",
        ))
    if question["interaction"] == "write_text":
        draft = _draft(db, session.id, question["id"])
        if draft:
            db.delete(draft)
    if should_advance:
        _advance(session, len(_question_ids(session)), has_pending=is_open, db=db)
    db.commit()
    db.refresh(session)
    return {
        "status": "ok",
        "submission": public_result,
        "lesson": _interaction_payload(db, session),
    }
