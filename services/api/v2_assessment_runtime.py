"""V2 pre/post assessment with official automatic placement and human audio review.

Objective evidence is corrected privately. Only recorded reading remains under
human review. After all 30 answers are graded, placement is a system action.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import json
from typing import Annotated, Any, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, File, Header, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field, StringConstraints
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
from db.models import AssessmentRetakeAuthorization, AssessmentSession, Attempt, AudioSubmission, AuditLog, ContentRelease, Student, User
from dependencies import get_current_user, get_db
from v2_content.importer import register_candidate_release
from v2_content.media import MediaProvider
from v2_content.projection import student_question
from v2_content.repository import get_release, get_pinned_release
from v2_content.recovery import known_recovery
from v2_interaction_runtime import AnswerRequest, CHOICE_INTERACTIONS, OPEN_INTERACTIONS, ORDER_INTERACTIONS, _canonical_answer, _ordered_answer_is_correct
from v2_lesson_runtime import _require_preview_student, _has_official_v2_placement
from v2_retry_state import active_retry
from v2_review_claims import enforce_review_claim, clear_review_claim
from v2_audio_rubric import ReadingRubricV2, save_v2_reading_rubric
from v2_audio_retention import (
    schedule_superseded_audio, run_retention_after_commit,
    audio_upload_binding, track_new_audio_upload, mark_audio_submitted,
)
from v2_audio_review_evidence import (
    AudioPlaybackCompletion, acknowledge_audio_playback,
    completed_audio_ids, require_audio_playback,
)


router = APIRouter(prefix="/v2/assessments", tags=["v2-assessments"])
POLICY_VERSION = "himma-v2-assessment/placement-threshold-50-80-v1"


def _recommended_level(score_percent: float | int | None) -> int | None:
    """Approved pretest placement boundaries (0<=score<=100), never a V1 level."""
    if score_percent is None:
        return None
    score = float(score_percent)
    if not 0 <= score <= 100:
        raise ValueError("pretest score outside approved percentage range")
    return 1 if score < 50 else 2 if score < 80 else 3


class DraftRequest(BaseModel):
    text: str = Field(max_length=500)


class ReviewRequest(BaseModel):
    is_correct: bool
    note: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=2000)]
    rubric: ReadingRubricV2 | None = None


class PlacementRequest(BaseModel):
    assigned_level: int = Field(ge=1, le=3)
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=2000)]
    override_recommendation: bool = False


def _empty_legacy_pretest(db: Session, student_id: int) -> AssessmentSession | None:
    """Recognize only an untouched V1 shell, never an actual historical attempt.

    The old start endpoint can leave a session before the first question. Keep
    its identity/history, but do not require academic review of absent evidence.
    GET only recognizes it; the explicit V2 start POST adopts it under the same
    student lock used by both assessment runtimes.
    """
    sessions = db.query(AssessmentSession).filter(AssessmentSession.student_id == student_id).limit(2).all()
    if len(sessions) != 1:
        return None
    row = sessions[0]
    if (row.session_type != "pretest" or row.status != "in_progress" or row.v2_state is not None
            or row.official_for_reporting or row.final_score is not None or row.assigned_level is not None
            or row.elapsed_seconds != 0 or row.v2_question_index != 0 or row.v2_result_json is not None
            or row.v2_policy_version is not None or row.completed_at is not None
            or row.assessment_attempt_no != 1 or row.supersedes_session_id is not None):
        return None
    if (db.query(StudentJourney.id).filter(StudentJourney.student_id == student_id).first()
            or db.query(LessonSession.id).filter(LessonSession.student_id == student_id).first()
            or db.query(Attempt.id).filter(Attempt.session_id == row.id).first()
            or db.query(AssessmentQuestionResponse.id).filter(AssessmentQuestionResponse.assessment_session_id == row.id).first()
            or db.query(AssessmentQuestionDraft.id).filter(AssessmentQuestionDraft.assessment_session_id == row.id).first()
            or db.query(PlacementDecisionV2.id).filter(PlacementDecisionV2.student_id == student_id).first()):
        return None
    return row


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
    # Only an officially placed, release-aligned lesson may appear as resumable.
    journey = db.query(StudentJourney).filter(StudentJourney.student_id == student.id).one_or_none()
    eligible_lesson = _has_official_v2_placement(db, student.id, journey)
    lesson = (db.query(LessonSession).filter(
        LessonSession.student_id == student.id,
        LessonSession.content_release_id == journey.content_release_id,
        LessonSession.status.in_(("in_progress", "waiting_review")),
    ).one_or_none() if eligible_lesson else None)
    if lesson:
        return {"action": "lesson", "state": lesson.stage, "href": f"/student/learning-v2/{lesson.id}", "label": "متابعة الدرس"}
    if not journey:
        # An account without a V2 journey is not necessarily a first-time
        # student. Never turn completed V1 evidence into a fresh V2 attempt.
        prior = db.query(AssessmentSession).filter(
            AssessmentSession.student_id == student.id,
        ).order_by(AssessmentSession.id.desc()).first()
        if prior and _empty_legacy_pretest(db, student.id) is None:
            previous_pretest = db.query(AssessmentSession).filter(
                AssessmentSession.student_id == student.id,
                AssessmentSession.session_type == "pretest",
            ).order_by(AssessmentSession.assessment_attempt_no.desc(), AssessmentSession.id.desc()).first()
            allowed_retake = previous_pretest and db.query(AssessmentRetakeAuthorization.id).filter(
                AssessmentRetakeAuthorization.student_id == student.id,
                AssessmentRetakeAuthorization.session_type == "pretest",
                AssessmentRetakeAuthorization.previous_session_id == previous_pretest.id,
                AssessmentRetakeAuthorization.status == "pending",
            ).first()
            if prior.status == "in_progress" or not allowed_retake:
                return {
                    "action": "migration_review", "href": None,
                    "label": "بانتظار مراجعة المشرف",
                }
    if not journey or journey.placement_state in {"not_started", "in_progress"}:
        return {"action": "start_pretest", "href": None, "label": "ابدأ الاختبار القبلي"}
    if journey.placement_state == "placed" and not eligible_lesson:
        return {"action": "placement_review", "href": None, "label": "بانتظار اعتماد التسكين"}
    if journey.placement_state == "posttest_ready":
        # Read-only projection; the same server-side academic gate authorizes
        # the actual POST. No supervisor switch is needed for a ready learner.
        return {"action": "start_posttest", "href": None, "label": "ابدأ الاختبار البعدي"}
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
    """One canonical pinned-bank resolver shared by assessments and lessons."""
    return get_pinned_release(db, session.content_release_id)


def blocked_review_item(db: Session, session, row, student: Student, error: HTTPException) -> dict:
    """Staff recovery metadata only; never replace a lost question with today's bank."""
    release = db.query(ContentRelease).filter(ContentRelease.id == session.content_release_id).one_or_none()
    return {"response_id": row.id, "session_id": session.id, "student_id": student.id,
            "student_name": student.name, "reason": "content_release_unavailable",
            "detail": str(error.detail), "content_release_id": session.content_release_id,
            "release_version": release.version if release else None,
            "release_checksum": release.checksum if release else None,
            "recoverable": bool(release and known_recovery(release.checksum) and not db.query(
                PrivateContentBankSnapshot.content_release_id,
            ).filter(PrivateContentBankSnapshot.content_release_id == release.id).first())}


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
        # Final graded evidence triggers autonomous placement; human reading
        # remains the only manual approval. Never infer a V1 academic level.
        if result["score_percent"] is None:
            raise HTTPException(status_code=409, detail="نتيجة القبلي لم تكتمل بعد")
        level = _recommended_level(result["score_percent"])
        journey = db.query(StudentJourney).filter(
            StudentJourney.student_id == session.student_id,
        ).with_for_update().one_or_none()
        if (journey is None or journey.content_release_id != session.content_release_id
                or journey.placement_state != "in_progress" or journey.status != "active"):
            raise HTTPException(status_code=409, detail="رحلة الطالب غير جاهزة للتسكين التلقائي")
        if db.query(PlacementDecisionV2.id).filter(
            PlacementDecisionV2.assessment_session_id == session.id,
        ).first() is not None:
            raise HTTPException(status_code=409, detail="قرار التسكين مسجل مسبقًا")
        release = _session_release(db, session)
        first_lesson = next((
            lesson["id"] for lesson in release["lessons"]
            if lesson["level"] == f"L{level}"
        ), None)
        if first_lesson is None:
            raise HTTPException(status_code=409, detail="لا يوجد درس مناسب في الإصدار المثبت")
        session.v2_state = "completed"
        session.status = "completed"
        session.completed_at = datetime.now(timezone.utc)
        session.final_score = result["score_percent"]
        session.assigned_level = level
        mark_official_completed_attempt(db, session)
        db.add(PlacementDecisionV2(
            student_id=session.student_id,
            assessment_session_id=session.id,
            content_release_id=session.content_release_id,
            assigned_level=level,
            reason="Auto placement from finalized official 30-question V2 pretest",
            policy_version=POLICY_VERSION,
            decided_by=None,  # Explicit system decision, never fake a staff actor
        ))
        journey.current_level = level
        journey.current_lesson_id = first_lesson
        journey.placement_state = "placed"
        student = db.query(Student).filter(Student.id == session.student_id).one()
        student.current_level = level  # Legacy identity mirror, not authority
        db.add(AuditLog(
            actor_role="system", actor_id=0, action="v2_automatic_placement",
            entity_type="assessment_session", entity_id=str(session.id),
            details=f"policy={POLICY_VERSION};recommended={level};score_percent={result['score_percent']};release_id={session.content_release_id}",
        ))
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
        if kind == "pretest" and _empty_legacy_pretest(db, student.id) is not None:
            # Preserve every original column in the audit before filling the
            # unused shell. No DELETE, fabricated result or completed V1 attempt.
            original = {column.name: getattr(active, column.name) for column in AssessmentSession.__table__.columns}
            release = register_candidate_release(db)
            active.content_release_id = release.id
            active.v2_state = "answering"
            active.v2_policy_version = POLICY_VERSION
            db.add(StudentJourney(student_id=student.id, content_release_id=release.id,
                                  placement_state="in_progress", current_level=1))
            db.add(AuditLog(actor_role="student", actor_id=student.id,
                            action="v2.pretest.empty_legacy_adopted", entity_type="assessment_session",
                            entity_id=str(active.id), details=json.dumps(original, default=str, sort_keys=True)))
            db.commit()
            db.refresh(active)
            return _payload(db, active)
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
    if kind == "posttest":
        # V2 learners enter the posttest on academic readiness, not a staff
        # approval flag. Keep the strict common gate for direct API calls.
        from v2_student_accounts import require_posttest_completion
        require_posttest_completion(db, student, journey, allow_completed=bool(authorization))
    # Once an academic journey exists, both later assessments keep its
    # immutable release rather than silently switching to the newest bank.
    release = (db.get(ContentRelease, journey.content_release_id)
               if journey is not None else register_candidate_release(db))
    if release is None:
        raise HTTPException(status_code=409, detail="إصدار رحلة الطالب الأصلي غير موجود")
    get_pinned_release(db, release.id)
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


@router.post("/sessions/{session_id}/finalize-placement")
def finalize_persisted_placement(
    session_id: int,
    student: Student = Depends(_require_preview_student),
    db: Session = Depends(get_db),
):
    """Recover an already-graded V2 pretest created before automatic placement.

    GETs remain read-only. A repeated POST is idempotent and returns the same
    official result. Incomplete or unreviewed audio can never create placement.
    """
    db.query(Student.id).filter(Student.id == student.id).with_for_update().one()
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.student_id == student.id,
        AssessmentSession.session_type == "pretest",
        AssessmentSession.v2_state.is_not(None),
    ).with_for_update().one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="جلسة القبلي غير موجودة")
    if session.v2_state == "completed" and session.official_for_reporting:
        return _payload(db, session)
    if (session.v2_state != "placement_pending_review"
            or session.status != "in_progress"
            or session.v2_question_index != 30):
        raise HTTPException(status_code=409, detail="جلسة القبلي ليست جاهزة لاستعادة التسكين")
    if db.query(PlacementDecisionV2.id).filter(
        PlacementDecisionV2.assessment_session_id == session.id,
    ).first() is not None:
        raise HTTPException(status_code=409, detail="قرار التسكين السابق يحتاج فحص اتساق")
    # _finish_if_ready verifies all 30 responses, pending audio and the
    # original immutable release before writing any academic placement.
    result = _result(db, session)
    if result["answered"] != 30 or result["pending_review"] or result["score_percent"] is None:
        raise HTTPException(status_code=409, detail="ينبغي إكمال الأسئلة ومراجعة تسجيلات القراءة أولًا")
    # A legacy "graded" flag alone is not proof that the child's actual
    # recording survived. Verify the pinned reading questions and the latest
    # graded recording before recovering an official placement decision.
    release = _session_release(db, session)
    required_reading = {
        row["id"] for row in release["questions"]
        if row["role"] == "pretest" and row["interaction"] == "read_aloud"
    }
    responses = db.query(AssessmentQuestionResponse).filter(
        AssessmentQuestionResponse.assessment_session_id == session.id,
    ).all()
    readings = [row for row in responses if row.question_id in required_reading]
    if ({row.question_id for row in readings} != required_reading
            or any(row.status != "graded" or row.is_correct is None for row in readings)):
        raise HTTPException(status_code=409, detail="لم تكتمل مراجعة تسجيلات القراءة الأصلية")
    reading_ids = [row.id for row in readings]
    recordings = db.query(AudioSubmission).filter(
        AudioSubmission.assessment_response_id.in_(reading_ids),
        AudioSubmission.status == "graded",
    ).order_by(AudioSubmission.id.desc()).all() if reading_ids else []
    latest = {}
    for audio in recordings:
        latest.setdefault(audio.assessment_response_id, audio)
    if len(latest) != len(readings):
        raise HTTPException(status_code=409, detail="الدليل الصوتي المعتمد مفقود؛ لم نُنشئ تسكينًا")
    for audio in latest.values():
        try:
            storage.verify_audio(audio.storage_key, audio.file_size, audio.mime_type)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail="ملف القراءة المعتمد غير موجود أو تغيّر") from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail="تعذر فحص التخزين الصوتي حاليًا") from exc
    _finish_if_ready(db, session)
    if session.v2_state != "completed":
        raise HTTPException(status_code=409, detail="لم يكتمل قرار التسكين التلقائي")
    db.commit()
    db.refresh(session)
    return _payload(db, session)


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
    binding_key = audio_upload_binding("assessment", session.id, question["id"])
    track_new_audio_upload(
        db, student_id=student.id, storage_key=key, binding_key=binding_key,
    )
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
            mark_audio_submitted(
                db,
                student_id=student.id,
                storage_key=canonical["audio_storage_key"],
                binding_key=audio_upload_binding("assessment", session.id, question["id"]),
            )
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
        "audio_submission_id": audio.id if is_reading and evidence_ready and audio else None,
        "audio_playback_completed": False,
        "evidence_ready": evidence_ready, "submitted_at": row.created_at.isoformat(),
    }


@router.get("/admin/review-queue")
def review_queue(
    limit: int = Query(default=50, ge=1, le=100), offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
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
    blocked_items = []
    for row, session, student in page:
        try:
            if session.content_release_id not in release_cache:
                release_cache[session.content_release_id] = _session_release(db, session)
            items.append(_review_item(
                db, row, session, student, release=release_cache[session.content_release_id],
                audio=audios.get(row.id), preloaded_audio=True,
            ))
        except HTTPException as error:
            if error.status_code != 409:
                raise
            blocked_items.append(blocked_review_item(db, session, row, student, error))
    response_audio_ids = {
        item["response_id"]: item["audio_submission_id"]
        for item in items if item["audio_submission_id"] is not None
    }
    completed = completed_audio_ids(
        db, kind="assessment", response_audio_ids=response_audio_ids, reviewer_id=user.id,
    )
    for item in items:
        item["audio_playback_completed"] = item["audio_submission_id"] in completed
    return {"items": items, "blocked_items": blocked_items, "next_offset": offset + limit if len(rows) > limit else None}


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


@router.post("/admin/responses/{response_id}/audio-completed")
def review_audio_completed(
    response_id: int,
    body: AudioPlaybackCompletion,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.query(AssessmentQuestionResponse).filter(
        AssessmentQuestionResponse.id == response_id,
    ).with_for_update().one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="الإجابة غير موجودة")
    if row.status != "pending_review":
        raise HTTPException(status_code=409, detail="هذه الإجابة لم تعد تنتظر مراجعة")
    enforce_review_claim(db, "assessment", row.id, user.id)
    session = _session(db, row.assessment_session_id)
    evidence = _review_item(db, row, session, db.query(Student).filter(Student.id == session.student_id).one())
    if evidence["interaction"] != "read_aloud":
        raise HTTPException(status_code=409, detail="هذه الإجابة ليست تسجيل قراءة")
    task = active_retry(db, assessment_response_id=row.id)
    audio = (
        db.query(AudioSubmission).filter(
            AudioSubmission.id == task.audio_submission_id,
            AudioSubmission.assessment_response_id == row.id,
        ).one_or_none()
        if task and task.status == "submitted" and task.audio_submission_id else
        db.query(AudioSubmission).filter(
            AudioSubmission.assessment_response_id == row.id,
        ).order_by(AudioSubmission.id.desc()).first()
    )
    if not audio or audio.status != "pending_review" or audio.id != body.audio_submission_id:
        raise HTTPException(status_code=409, detail="نسخة التسجيل تغيرت؛ حدّث قائمة المراجعة")
    acknowledge_audio_playback(
        db, kind="assessment", response_id=row.id,
        audio_submission_id=audio.id, reviewer_id=user.id,
    )
    db.commit()
    return {"status": "playback_completed", "audio_submission_id": audio.id}


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
            "attempt_no": session.assessment_attempt_no,
            "result": {
                **_result_from_rows(grouped[session.id]),
                "recommended_level": _recommended_level(
                    _result_from_rows(grouped[session.id])["score_percent"]
                ),
            },
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
        require_audio_playback(
            db, kind="assessment", response_id=row.id,
            audio_submission_id=audio_to_verify.id, reviewer_id=user.id,
        )
    row.status = "graded"; row.is_correct = body.is_correct; row.review_note = body.note
    row.reviewed_by = user.id; row.reviewed_at = datetime.now(timezone.utc)
    audio = (db.query(AudioSubmission).filter(AudioSubmission.id == task.audio_submission_id).one_or_none()
             if task and task.audio_submission_id else
             db.query(AudioSubmission).filter(AudioSubmission.assessment_response_id == row.id).order_by(AudioSubmission.id.desc()).first())
    if audio: audio.status = "graded"
    if evidence["interaction"] == "read_aloud" and audio:
        save_v2_reading_rubric(db, audio=audio, reviewer_id=user.id, rubric=body.rubric)
    elif body.rubric is not None:
        raise HTTPException(status_code=422, detail="معيار القراءة غير متاح إلا للإجابة الصوتية")
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
    """Retired V2 manual placement route; no staff-directed academic writes.

    Older pretests are reconciled through the authenticated student's
    idempotent /sessions/{id}/finalize-placement route using official evidence.
    Human reviewers may still grade audio, never choose a learning level.
    """
    raise HTTPException(
        status_code=409,
        detail="التسكين في هِمّة تلقائي بعد مراجعة تسجيلات القراءة؛ لا يُقبل اعتماد مستوى يدوي",
    )


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
