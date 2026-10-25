"""P06 candidate pre/post runtime and supervisor review boundary.

The bank is complete (30+30), but placement thresholds are not academically
approved. Therefore objective evidence is graded privately, open evidence is
human-reviewed, and pretest placement is an explicit audited supervisor act.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, File, Header, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

import storage
import recordings
from assessment_retake import mark_official_completed_attempt
from db.learning_models import (
    AssessmentQuestionDraft,
    AssessmentQuestionResponse,
    PlacementDecisionV2,
    StudentJourney,
    LessonSession,
    PrivateContentBankSnapshot,
)
from db.models import AssessmentRetakeAuthorization, AssessmentSession, AudioSubmission, AuditLog, ContentRelease, Student, User
from dependencies import get_current_user, get_db
from v2_content.importer import register_candidate_release
from v2_content.media import MediaProvider
from v2_content.projection import student_question
from v2_content.repository import get_release
from v2_interaction_runtime import AnswerRequest, CHOICE_INTERACTIONS, OPEN_INTERACTIONS, ORDER_INTERACTIONS, _canonical_answer, _ordered_answer_is_correct
from v2_lesson_runtime import _require_preview_student
from v2_retry_state import active_retry
from v2_review_claims import enforce_review_claim, clear_review_claim
from v2_audio_retention import (
    schedule_superseded_audio, run_retention_after_commit,
    track_new_audio_upload, mark_audio_submitted,
)


router = APIRouter(prefix="/v2/assessments", tags=["v2-assessments"])
POLICY_VERSION = "himma-v2-assessment/manual-placement-1-candidate"


class DraftRequest(BaseModel):
    text: str = Field(max_length=500)


class ReviewRequest(BaseModel):
    is_correct: bool
    note: str = Field(min_length=2, max_length=2000)


class PlacementRequest(BaseModel):
    assigned_level: int = Field(ge=1, le=3)
    reason: str = Field(min_length=10, max_length=2000)


@router.get("/current-action")
def current_action(student: Student = Depends(_require_preview_student), db: Session = Depends(get_db)):
    """One read-only, exhaustive resume decision for the learner dashboard."""
    assessment = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student.id,
        AssessmentSession.status == "in_progress",
        AssessmentSession.v2_state.is_not(None),
    ).order_by(AssessmentSession.started_at.desc()).first()
    if assessment:
        return {
            "action": "assessment",
            "kind": assessment.session_type,
            "state": assessment.v2_state,
            "href": f"/student/assessment-v2/{assessment.id}",
            "label": "متابعة الاختبار" if assessment.v2_state == "answering" else "عرض حالة المراجعة",
        }
    journey = db.query(StudentJourney).filter(StudentJourney.student_id == student.id).one_or_none()
    if not journey or journey.placement_state in {"not_started", "in_progress"}:
        return {"action": "start_pretest", "href": None, "label": "ابدأ الاختبار القبلي"}
    lesson = db.query(LessonSession).filter(
        LessonSession.student_id == student.id,
        LessonSession.status.in_(("in_progress", "waiting_review")),
    ).one_or_none()
    if lesson:
        return {"action": "lesson", "state": lesson.stage, "href": f"/student/learning-v2/{lesson.id}", "label": "متابعة الدرس"}
    if journey.placement_state == "posttest_ready":
        return {"action": "start_posttest" if student.posttest_enabled else "waiting_posttest_enable", "href": None, "label": "ابدأ الاختبار البعدي" if student.posttest_enabled else "بانتظار إتاحة الاختبار البعدي"}
    if journey.placement_state == "completed":
        return {"action": "complete", "href": "/student/learning-v2", "label": "اكتملت الرحلة"}
    return {"action": "lesson_catalog", "href": "/student/learning-v2", "label": "متابعة الرحلة التعليمية"}


def _ids(role: str, release: dict[str, Any]) -> list[str]:
    return [q["id"] for q in release["questions"] if q["role"] == role]


def _session(db: Session, session_id: int, student_id: int | None = None) -> AssessmentSession:
    query = db.query(AssessmentSession).filter(AssessmentSession.id == session_id, AssessmentSession.v2_state.is_not(None))
    if student_id is not None:
        query = query.filter(AssessmentSession.student_id == student_id)
    row = query.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="جلسة التقييم غير موجودة")
    return row


def _current(db: Session, session: AssessmentSession) -> dict[str, Any]:
    release = _session_release(db, session)
    ids = _ids(session.session_type, release)
    if session.v2_question_index >= len(ids):
        raise HTTPException(status_code=409, detail="اكتملت أسئلة هذه الجلسة")
    question = next((row for row in release["questions"] if row["id"] == ids[session.v2_question_index]), None)
    if not question:
        raise HTTPException(status_code=409, detail="سؤال التقييم غير موجود في الإصدار")
    return question


def _session_release(db: Session, session: AssessmentSession) -> dict[str, Any]:
    """Resolve the original immutable bank for this exact assessment attempt.

    Earlier candidates without a snapshot may read the current compiled bank
    only when the stored checksum still matches. Never silently remap an old
    student attempt onto a newer bank.
    """
    record = db.query(ContentRelease).filter(ContentRelease.id == session.content_release_id).one_or_none()
    if not record:
        raise HTTPException(status_code=409, detail="إصدار أسئلة هذه الجلسة غير مسجل")
    frozen = db.query(PrivateContentBankSnapshot).filter(
        PrivateContentBankSnapshot.content_release_id == record.id,
    ).one_or_none()
    if frozen:
        snapshot = frozen.payload_json
        if frozen.checksum != record.checksum or snapshot.get("checksum") != record.checksum or snapshot.get("version") != record.version:
            raise HTTPException(status_code=409, detail="بصمة محتوى الجلسة لا تطابق النسخة المحفوظة")
        return snapshot
    current = get_release()
    if record.checksum == current["checksum"] and record.version == current["version"]:
        return current
    raise HTTPException(status_code=409, detail="النسخة الأصلية غير محفوظة؛ تم إيقاف التقييم لحماية الإجابات")


def _media(question: dict[str, Any], release: dict[str, Any]) -> dict[str, dict[str, Any]]:
    ids = {m["media_id"] for m in question.get("stimulus", {}).get("media", [])}
    ids |= {m["media_id"] for option in question.get("options", []) for m in option.get("media", [])}
    result: dict[str, dict[str, Any]] = {}
    provider = MediaProvider()
    for media_id in sorted(ids):
        asset = next((row for row in release["media"] if row["id"] == media_id), None)
        if not asset:
            raise HTTPException(status_code=409, detail="أحد أصول التقييم غير مسجل")
        result[media_id] = provider.resolve(asset).as_dict()
    return result


def _result(db: Session, session: AssessmentSession) -> dict[str, Any]:
    rows = db.query(AssessmentQuestionResponse).filter(AssessmentQuestionResponse.assessment_session_id == session.id).all()
    return _result_from_rows(rows)


def _result_from_rows(rows: list[AssessmentQuestionResponse]) -> dict[str, Any]:
    pending = sum(row.status == "pending_review" for row in rows)
    skill: dict[str, dict[str, int]] = defaultdict(lambda: {"graded": 0, "correct": 0, "pending": 0})
    for row in rows:
        bucket = skill[row.skill_group]
        if row.status == "pending_review":
            bucket["pending"] += 1
        else:
            bucket["graded"] += 1
            bucket["correct"] += int(row.is_correct is True)
    correct = sum(row.is_correct is True for row in rows)
    return {
        "answered": len(rows),
        "total": 30,
        "pending_review": pending,
        "correct": correct if not pending and len(rows) == 30 else None,
        "score_percent": round(correct / 30 * 100, 2) if not pending and len(rows) == 30 else None,
        "skills": dict(sorted(skill.items())),
    }


def _payload(db: Session, session: AssessmentSession) -> dict[str, Any]:
    result = _result(db, session)
    payload: dict[str, Any] = {
        "session": {
            "session_id": session.id,
            "kind": session.session_type,
            "state": session.v2_state,
            "status": session.status,
            "progress": {"answered": result["answered"], "total": 30},
            "release_id": session.content_release_id,
            "attempt_no": session.assessment_attempt_no,
        },
        "summary": {"pending_review": result["pending_review"]},
        "interaction": None,
    }
    if session.v2_state == "answering":
        question = _current(db, session)
        draft = db.query(AssessmentQuestionDraft).filter(
            AssessmentQuestionDraft.assessment_session_id == session.id,
            AssessmentQuestionDraft.question_id == question["id"],
        ).one_or_none()
        payload["interaction"] = {
            "question": student_question(question),
            "media": _media(question, _session_release(db, session)),
            "progress": {"index": session.v2_question_index + 1, "total": 30, "stage": session.session_type},
            "attempts": 0,
            "draft": (draft.draft_json or {}).get("text") if draft else None,
        }
    if session.v2_state == "completed" and session.session_type == "posttest":
        payload["outcome"] = session.v2_result_json
    return payload


def _finish_if_ready(db: Session, session: AssessmentSession) -> None:
    if session.v2_question_index < 30:
        return
    result = _result(db, session)
    if result["answered"] != 30:
        raise HTTPException(status_code=409, detail="بيانات التقييم ناقصة؛ لا يمكن إكمال جلسة غير مكتملة")
    session.v2_result_json = result
    if result["pending_review"]:
        session.v2_state = "waiting_review"
        return
    if session.session_type == "pretest":
        session.v2_state = "placement_pending_review"
        return
    session.v2_state = "completed"
    session.status = "completed"
    session.completed_at = datetime.now(timezone.utc)
    session.final_score = result["score_percent"]
    mark_official_completed_attempt(db, session)
    journey = db.query(StudentJourney).filter(StudentJourney.student_id == session.student_id).one_or_none()
    if journey:
        journey.placement_state = "completed"
        journey.status = "completed"
    student = db.query(Student).filter(Student.id == session.student_id).one()
    student.posttest_enabled = False


@router.post("/{kind}/start")
def start_assessment(
    kind: Literal["pretest", "posttest"],
    student: Student = Depends(_require_preview_student),
    db: Session = Depends(get_db),
):
    # Serialize V1/V2 assessment starts for the same student (PostgreSQL).
    db.query(Student).filter(Student.id == student.id).with_for_update().one()
    active = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student.id,
        AssessmentSession.status == "in_progress",
    ).one_or_none()
    if active:
        if active.v2_state is None or active.session_type != kind:
            raise HTTPException(status_code=409, detail="لديك جلسة أخرى قيد التنفيذ")
        return _payload(db, active)
    journey = db.query(StudentJourney).filter(StudentJourney.student_id == student.id).one_or_none()
    # V1 and V2 share the same attempt history and uniqueness index. A V1
    # completed assessment must never be bypassed as a first V2 attempt.
    previous = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student.id,
        AssessmentSession.session_type == kind,
    ).order_by(AssessmentSession.assessment_attempt_no.desc(), AssessmentSession.id.desc()).first()
    authorization = None
    if previous:
        authorization = db.query(AssessmentRetakeAuthorization).filter(
            AssessmentRetakeAuthorization.student_id == student.id,
            AssessmentRetakeAuthorization.session_type == kind,
            AssessmentRetakeAuthorization.previous_session_id == previous.id,
            AssessmentRetakeAuthorization.status == "pending",
        ).one_or_none()
        if not authorization:
            raise HTTPException(status_code=409, detail="إعادة التقييم تحتاج تفويضًا صريحًا من المشرف")
    if kind == "pretest" and not authorization and journey and journey.placement_state not in {"not_started", "in_progress"}:
        raise HTTPException(status_code=409, detail="اكتمل الاختبار القبلي والتسكين")
    if kind == "posttest" and not journey:
        raise HTTPException(status_code=409, detail="لا توجد رحلة V2 جاهزة للاختبار البعدي")
    if kind == "posttest" and not authorization and (not journey or journey.placement_state != "posttest_ready" or not student.posttest_enabled):
        raise HTTPException(status_code=409, detail="الاختبار البعدي غير متاح بعد")
    release = register_candidate_release(db)
    if journey is None:
        journey = StudentJourney(student_id=student.id, content_release_id=release.id, placement_state="in_progress", current_level=1)
        db.add(journey)
    elif journey.content_release_id != release.id:
        raise HTTPException(status_code=409, detail="رحلة الطالب مثبتة على إصدار مختلف")
    elif kind == "pretest":
        journey.placement_state = "in_progress"
    session = AssessmentSession(
        student_id=student.id,
        content_release_id=release.id,
        session_type=kind,
        status="in_progress",
        v2_state="answering",
        v2_policy_version=POLICY_VERSION,
        assessment_attempt_no=(previous.assessment_attempt_no + 1) if previous else 1,
        supersedes_session_id=previous.id if previous else None,
    )
    db.add(session)
    db.flush()
    if authorization:
        authorization.status = "consumed"
        authorization.consumed_at = datetime.now(timezone.utc)
        authorization.new_session_id = session.id
    db.commit()
    db.refresh(session)
    return _payload(db, session)


@router.get("/sessions/{session_id}")
def assessment_session(session_id: int, student: Student = Depends(_require_preview_student), db: Session = Depends(get_db)):
    return _payload(db, _session(db, session_id, student.id))


@router.put("/sessions/{session_id}/draft")
def save_draft(session_id: int, body: DraftRequest, student: Student = Depends(_require_preview_student), db: Session = Depends(get_db)):
    session = _session(db, session_id, student.id)
    question = _current(db, session)
    if question["interaction"] != "write_text":
        raise HTTPException(status_code=409, detail="المسودة متاحة لسؤال الكتابة فقط")
    row = db.query(AssessmentQuestionDraft).filter(
        AssessmentQuestionDraft.assessment_session_id == session.id,
        AssessmentQuestionDraft.question_id == question["id"],
    ).one_or_none()
    if row:
        row.draft_json = {"text": body.text}; row.version += 1; row.updated_at = datetime.now(timezone.utc)
    else:
        row = AssessmentQuestionDraft(assessment_session_id=session.id, question_id=question["id"], draft_json={"text": body.text})
        db.add(row)
    db.commit()
    return {"status": "saved", "question_id": question["id"], "version": row.version}


@router.post("/sessions/{session_id}/recording")
def upload_recording(
    session_id: int,
    file: UploadFile = File(...),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=8, max_length=100),
    student: Student = Depends(_require_preview_student),
    db: Session = Depends(get_db),
):
    session = _session(db, session_id, student.id)
    question = _current(db, session)
    if question["interaction"] != "read_aloud" or not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="التسجيل غير صالح للسؤال الحالي")
    try:
        key, size, _ = storage.upload_audio(file, student.id, f"v2-assessment:{session.id}:{question['id']}:{idempotency_key}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="ملف التسجيل غير صالح") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="خدمة حفظ التسجيلات غير متاحة الآن") from exc
    track_new_audio_upload(db, student_id=student.id, storage_key=key)
    db.commit()
    return {"audio_storage_key": key, "audio_file_size": size, "audio_mime_type": file.content_type}


@router.post("/sessions/{session_id}/answers")
def answer(session_id: int, body: AnswerRequest, student: Student = Depends(_require_preview_student), db: Session = Depends(get_db)):
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.student_id == student.id,
        AssessmentSession.v2_state.is_not(None),
    ).with_for_update().one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="جلسة التقييم غير موجودة")
    existing = db.query(AssessmentQuestionResponse).filter(
        AssessmentQuestionResponse.assessment_session_id == session.id,
        AssessmentQuestionResponse.submit_key == body.submit_key,
    ).one_or_none()
    if existing:
        release = _session_release(db, session)
        candidate = next((q for q in release["questions"] if q["id"] == existing.question_id), None)
        if not candidate or existing.answer_json != _canonical_answer(candidate, body, student.id):
            raise HTTPException(status_code=409, detail="مفتاح الإرسال استُخدم لإجابة مختلفة")
        return {"status": "replayed", "submission": {"status": existing.status, "accepted": True}, "assessment": _payload(db, session)}
    if session.v2_state != "answering":
        raise HTTPException(status_code=409, detail="الجلسة لا تقبل إجابات الآن")
    question = _current(db, session)
    canonical = _canonical_answer(question, body, student.id)
    is_open = question["interaction"] in OPEN_INTERACTIONS
    expected = question["private_answer"]["correct_option_ids"]
    if is_open:
        correct = None
    elif question["interaction"] in ORDER_INTERACTIONS:
        correct = _ordered_answer_is_correct(question, canonical["selected_option_ids"])
    else:
        correct = set(canonical["selected_option_ids"]) == set(expected)
    response = AssessmentQuestionResponse(
        assessment_session_id=session.id, question_id=question["id"], role=session.session_type,
        answer_json=canonical, submit_key=body.submit_key, status="pending_review" if is_open else "graded",
        is_correct=correct, skill_group=question["skill_group"], evidence_type=question["evidence_type"],
    )
    db.add(response); db.flush()
    if question["interaction"] == "read_aloud":
        try:
            mark_audio_submitted(db, student_id=student.id, storage_key=canonical["audio_storage_key"])
        except ValueError as exc:
            raise HTTPException(status_code=409, detail="ملف التسجيل المؤقت لم يعد صالحًا للإرسال") from exc
        db.add(AudioSubmission(
            response_id=None, lesson_response_id=None, assessment_response_id=response.id,
            storage_key=canonical["audio_storage_key"], file_size=canonical["audio_file_size"],
            mime_type=canonical["audio_mime_type"], duration_seconds=canonical["audio_duration_seconds"], status="pending_review",
        ))
    if question["interaction"] == "write_text":
        draft = db.query(AssessmentQuestionDraft).filter(
            AssessmentQuestionDraft.assessment_session_id == session.id,
            AssessmentQuestionDraft.question_id == question["id"],
        ).one_or_none()
        if draft: db.delete(draft)
    session.v2_question_index += 1
    session.updated_at = datetime.now(timezone.utc)
    _finish_if_ready(db, session)
    db.commit(); db.refresh(session)
    return {
        "status": "ok",
        "submission": {"status": response.status, "accepted": True, "retry_required": False, "message": "تم حفظ إجابتك." if not is_open else "حُفظت إجابتك وتنتظر مراجعة المشرف."},
        "assessment": _payload(db, session),
    }


def _review_item(
    db: Session, row: AssessmentQuestionResponse, session: AssessmentSession, student: Student,
    *, release: dict[str, Any] | None = None, audio: AudioSubmission | None = None, preloaded_audio: bool = False,
) -> dict[str, Any]:
    release = release if release is not None else _session_release(db, session)
    question = next((q for q in release["questions"] if q["id"] == row.question_id), None)
    if not question or question["role"] != row.role:
        raise HTTPException(status_code=409, detail="سؤال المراجعة لا يطابق الإصدار")
    task = active_retry(db, assessment_response_id=row.id)
    if task:
        if task.status == "submitted":
            audio = db.query(AudioSubmission).filter(
                AudioSubmission.id == task.audio_submission_id,
                AudioSubmission.assessment_response_id == row.id,
            ).one_or_none() if task.audio_submission_id else None
        else:
            audio = None
    elif not preloaded_audio:
        audio = db.query(AudioSubmission).filter(
            AudioSubmission.assessment_response_id == row.id
        ).order_by(AudioSubmission.id.desc()).first()
    answer = (task.replacement_json if task and task.status == "submitted" else row.answer_json) or {}
    is_reading = question["interaction"] == "read_aloud"
    is_writing = question["interaction"] == "write_text"
    evidence_ready = bool(
        audio and audio.status == "pending_review" and audio.file_size > 0
        and audio.storage_key.startswith(f"audio/{session.student_id}/")
    ) if is_reading else bool(answer.get("text_response", "").strip()) if is_writing else False
    if task and task.status == "requested":
        evidence_ready = False
    return {
        "response_id": row.id, "retry_state": task.status if task else None,
        "session_id": session.id, "student_id": student.id,
        "student_name": student.name, "question_id": row.question_id,
        "kind": row.role, "skill_group": row.skill_group, "evidence_type": row.evidence_type,
        "interaction": question["interaction"], "prompt": question["prompt"],
        "stimulus_text": (question.get("stimulus") or {}).get("text"),
        "reference": question.get("reading_reference") if is_reading else None,
        "rubric": (question.get("private_answer") or {}).get("rubric"),
        "text_response": answer.get("text_response") if is_writing else None,
        "audio_url": f"/api/v2/assessments/admin/responses/{row.id}/audio" if is_reading and evidence_ready else None,
        "evidence_ready": evidence_ready, "submitted_at": row.created_at.isoformat(),
    }


@router.get("/admin/review-queue")
def review_queue(
    limit: int = Query(default=50, ge=1, le=100), offset: int = Query(default=0, ge=0),
    _user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    query = db.query(AssessmentQuestionResponse, AssessmentSession, Student).join(
        AssessmentSession, AssessmentQuestionResponse.assessment_session_id == AssessmentSession.id
    ).join(Student, Student.id == AssessmentSession.student_id).filter(
        AssessmentQuestionResponse.status == "pending_review", AssessmentSession.v2_state.is_not(None),
    )
    rows = query.order_by(AssessmentQuestionResponse.created_at, AssessmentQuestionResponse.id).offset(offset).limit(limit + 1).all()
    page = rows[:limit]
    release_cache: dict[int, dict[str, Any]] = {}
    response_ids = [row.id for row, _, _ in page]
    audios = {
        audio.assessment_response_id: audio for audio in db.query(AudioSubmission).filter(
            AudioSubmission.assessment_response_id.in_(response_ids),
        ).order_by(AudioSubmission.id).all()
    } if response_ids else {}
    items = []
    for row, session, student in page:
        if session.content_release_id not in release_cache:
            release_cache[session.content_release_id] = _session_release(db, session)
        items.append(_review_item(
            db, row, session, student, release=release_cache[session.content_release_id],
            audio=audios.get(row.id), preloaded_audio=True,
        ))
    return {"items": items, "next_offset": offset + limit if len(rows) > limit else None}


@router.get("/admin/responses/{response_id}/audio")
def review_audio(
    response_id: int,
    range_header: str | None = Header(default=None, alias="Range"),
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    row = db.query(AssessmentQuestionResponse).filter(AssessmentQuestionResponse.id == response_id).one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="الإجابة غير موجودة")
    session = _session(db, row.assessment_session_id)
    release = _session_release(db, session)
    question = next((q for q in release["questions"] if q["id"] == row.question_id), None)
    if not question or question["interaction"] != "read_aloud":
        raise HTTPException(status_code=404, detail="لا يوجد تسجيل لهذا السؤال")
    task = active_retry(db, assessment_response_id=row.id)
    if task and task.status == "requested":
        raise HTTPException(status_code=404, detail="انتظار إعادة تسجيل الطالب")
    if task:
        audio = db.query(AudioSubmission).filter(
            AudioSubmission.id == task.audio_submission_id,
            AudioSubmission.assessment_response_id == row.id,
        ).one_or_none() if task.audio_submission_id else None
    else:
        audio = db.query(AudioSubmission).filter(
            AudioSubmission.assessment_response_id == row.id,
        ).order_by(AudioSubmission.id.desc()).first()
    if not audio or not audio.storage_key.startswith(f"audio/{session.student_id}/"):
        raise HTTPException(status_code=404, detail="تسجيل الطالب غير متاح")
    return recordings.play_by_key(key=audio.storage_key, range_header=range_header, researcher=user)


@router.get("/admin/placement-queue")
def placement_queue(
    limit: int = Query(default=50, ge=1, le=100), offset: int = Query(default=0, ge=0),
    _user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    rows = db.query(AssessmentSession, Student).join(Student, Student.id == AssessmentSession.student_id).filter(
        AssessmentSession.session_type == "pretest", AssessmentSession.v2_state == "placement_pending_review",
    ).order_by(AssessmentSession.started_at, AssessmentSession.id).offset(offset).limit(limit + 1).all()
    page = rows[:limit]
    session_ids = [session.id for session, _ in page]
    grouped: dict[int, list[AssessmentQuestionResponse]] = defaultdict(list)
    if session_ids:
        for response in db.query(AssessmentQuestionResponse).filter(
            AssessmentQuestionResponse.assessment_session_id.in_(session_ids),
        ).all():
            grouped[response.assessment_session_id].append(response)
    return {
        "items": [{
            "session_id": session.id, "student_id": student.id, "student_name": student.name,
            "attempt_no": session.assessment_attempt_no, "result": _result_from_rows(grouped[session.id]),
        } for session, student in page],
        "next_offset": offset + limit if len(rows) > limit else None,
    }


@router.post("/admin/responses/{response_id}/review")
def review_response(response_id: int, body: ReviewRequest, background_tasks: BackgroundTasks, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.query(AssessmentQuestionResponse).filter(AssessmentQuestionResponse.id == response_id).with_for_update().one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="الإجابة غير موجودة")
    if row.status != "pending_review":
        raise HTTPException(status_code=409, detail="تمت مراجعة الإجابة سابقًا")
    enforce_review_claim(db, "assessment", row.id, user.id)
    session = _session(db, row.assessment_session_id)
    student = db.query(Student).filter(Student.id == session.student_id).one()
    evidence = _review_item(db, row, session, student)
    if not evidence["evidence_ready"]:
        raise HTTPException(status_code=409, detail="لا يمكن تقييم إجابة دون دليل صوتي أو كتابي صالح")
    task = active_retry(db, assessment_response_id=row.id)
    if task and task.status == "requested":
        raise HTTPException(status_code=409, detail="الإجابة تنتظر إعادة دليل الطالب")
    if evidence["interaction"] == "read_aloud":
        if task:
            audio_to_verify = db.query(AudioSubmission).filter(
                AudioSubmission.id == task.audio_submission_id,
                AudioSubmission.assessment_response_id == row.id,
            ).one()
        else:
            audio_to_verify = db.query(AudioSubmission).filter(
                AudioSubmission.assessment_response_id == row.id,
            ).order_by(AudioSubmission.id.desc()).first()
        if audio_to_verify is None:
            raise HTTPException(status_code=409, detail="ملف التسجيل غير موجود")
        try:
            storage.verify_audio(audio_to_verify.storage_key, audio_to_verify.file_size, audio_to_verify.mime_type)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail="ملف التسجيل الصوتي مفقود أو تغير بعد إرساله") from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail="تعذر التحقق من التسجيل؛ يرجى إعادة المحاولة") from exc
    row.status = "graded"; row.is_correct = body.is_correct; row.review_note = body.note
    row.reviewed_by = user.id; row.reviewed_at = datetime.now(timezone.utc)
    audio = (db.query(AudioSubmission).filter(AudioSubmission.id == task.audio_submission_id).one_or_none()
             if task and task.audio_submission_id else
             db.query(AudioSubmission).filter(AudioSubmission.assessment_response_id == row.id).order_by(AudioSubmission.id.desc()).first())
    if audio: audio.status = "graded"
    if evidence["interaction"] == "read_aloud" and audio:
        extra = tuple(
            item.get("audio_storage_key") for item in ((task.replacement_json or {}).get("superseded_staged_audio") or [])
            if item.get("audio_storage_key")
        ) if task and isinstance(task.replacement_json, dict) else ()
        schedule_superseded_audio(
            db, student_id=student.id, question_id=row.question_id,
            winning_audio_id=audio.id, kind=session.session_type,
            extra_staged_keys=extra,
        )
    if task and task.status == "submitted":
        task.status = "resolved"
        task.resolved_at = datetime.now(timezone.utc)
    clear_review_claim(db, "assessment", row.id)
    _finish_if_ready(db, session)
    db.add(AuditLog(actor_role="researcher", actor_id=user.id, action="v2_assessment_response_reviewed", entity_type="assessment_question_response", entity_id=str(row.id), details=f"is_correct={body.is_correct}; note_location=assessment_question_responses.review_note"))
    db.commit()
    if evidence["interaction"] == "read_aloud" and audio:
        background_tasks.add_task(run_retention_after_commit)
    return {"status": "graded", "session_state": session.v2_state}


@router.post("/admin/sessions/{session_id}/placement")
def place_student(session_id: int, body: PlacementRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id, AssessmentSession.v2_state.is_not(None),
    ).with_for_update().one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="جلسة التقييم غير موجودة")
    if session.session_type != "pretest" or session.v2_state != "placement_pending_review":
        raise HTTPException(status_code=409, detail="الجلسة غير جاهزة للتسكين")
    if db.query(PlacementDecisionV2).filter(PlacementDecisionV2.assessment_session_id == session.id).first():
        raise HTTPException(status_code=409, detail="تم اعتماد التسكين سابقًا")
    release = _session_release(db, session)
    first_lesson = next(row["id"] for row in release["lessons"] if row["level"] == f"L{body.assigned_level}")
    journey = db.query(StudentJourney).filter(StudentJourney.student_id == session.student_id).one()
    student = db.query(Student).filter(Student.id == session.student_id).one()
    result = _result(db, session)
    if result["answered"] != 30 or result["pending_review"] or result["score_percent"] is None:
        raise HTTPException(status_code=409, detail="لا يمكن تسكين طالب قبل اكتمال التقييم ومراجعة جميع الأدلة")
    db.add(PlacementDecisionV2(student_id=student.id, assessment_session_id=session.id, content_release_id=session.content_release_id, assigned_level=body.assigned_level, reason=body.reason, policy_version=POLICY_VERSION, decided_by=user.id))
    session.assigned_level = body.assigned_level; session.final_score = result["score_percent"]
    session.v2_result_json = result; session.v2_state = "completed"; session.status = "completed"
    session.completed_at = datetime.now(timezone.utc)
    mark_official_completed_attempt(db, session)
    journey.current_level = body.assigned_level; journey.current_lesson_id = first_lesson; journey.placement_state = "placed"
    student.current_level = body.assigned_level
    db.add(AuditLog(actor_role="researcher", actor_id=user.id, action="v2_manual_placement_approved", entity_type="assessment_session", entity_id=str(session.id), details=f"level={body.assigned_level}; policy={POLICY_VERSION}; reason={body.reason}"))
    db.commit()
    return {"status": "placed", "assigned_level": body.assigned_level, "current_lesson_id": first_lesson}


def _session_report(db: Session, session: AssessmentSession) -> dict[str, Any]:
    release = db.query(ContentRelease).filter(ContentRelease.id == session.content_release_id).one_or_none()
    return {
        "session_id": session.id, "kind": session.session_type, "state": session.v2_state,
        "attempt_no": session.assessment_attempt_no, "official": session.official_for_reporting,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "elapsed_seconds": session.elapsed_seconds, "release_version": release.version if release else None,
        "result": _result(db, session), "assigned_level": session.assigned_level,
    }


@router.get("/admin/students/{student_id}/summary")
def student_summary(student_id: int, _user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).one_or_none()
    if not student: raise HTTPException(status_code=404, detail="الطالب غير موجود")
    sessions = db.query(AssessmentSession).filter(AssessmentSession.student_id == student.id, AssessmentSession.v2_state.is_not(None)).order_by(AssessmentSession.started_at).all()
    journey = db.query(StudentJourney).filter(StudentJourney.student_id == student.id).one_or_none()
    return {"student": {"id": student.id, "name": student.name, "current_level": student.current_level}, "journey": {"placement_state": journey.placement_state, "current_lesson_id": journey.current_lesson_id} if journey else None, "assessments": [_session_report(db, row) for row in sessions]}


@router.get("/admin/reports/summary")
def reports_summary(_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    counts = db.query(AssessmentSession.session_type, AssessmentSession.v2_state, func.count(AssessmentSession.id)).filter(
        AssessmentSession.v2_state.is_not(None),
    ).group_by(AssessmentSession.session_type, AssessmentSession.v2_state).all()
    averages = db.query(AssessmentSession.session_type, func.avg(AssessmentSession.final_score)).filter(
        AssessmentSession.v2_state.is_not(None), AssessmentSession.status == "completed",
        AssessmentSession.official_for_reporting.is_(True), AssessmentSession.final_score.is_not(None),
        AssessmentSession.session_type.in_(("pretest", "posttest")),
    ).group_by(AssessmentSession.session_type).all()
    result: dict[str, Any] = {
        "counts": {f"{kind}:{state}": count for kind, state, count in counts},
        "averages": {"pretest": None, "posttest": None},
    }
    for kind, mean in averages:
        result["averages"][kind] = round(float(mean), 2) if mean is not None else None
    result["missing_policy"] = "null_not_zero"
    return result
