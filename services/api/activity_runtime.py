"""Canonical adaptive-learning HTTP runtime.

This module owns the mounted ``/activities`` routes and keeps academic evidence
state separate from learner navigation state:

- uploaded/pending audio is persisted evidence awaiting supervisor review;
- pending audio never becomes correctness/mastery/completion evidence;
- a learner may continue to another approved item while review is pending;
- ``rerecord_required`` is deferred until the learner explicitly opens that task;
- rerecording creates a new audio submission and preserves the rejected one;
- ``graded`` is the only audio-review state that may complete the reading step;
- unresolved audio may hold promotion/level completion but not same-level study.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import storage
from activities import (
    ActivitySubmitRequest,
    _activity_session_or_404,
    _finalize_session_if_done,
    _load_item,
    _progress_payload,
    _rich_item_query,
    _step_payload as stage2_step_payload,
    _step_state as stage2_step_state,
    learning_status as stage2_learning_status,
    start_learning as stage2_start_learning,
    submit_activity_step as stage2_submit_activity_step,
)
from activities_v4 import _preferred_core_skill_id, _resolve_active_session
from adaptation_runtime import prepare_next_for_student
from assessment import (
    _commit_idempotent,
    _idempotency_replay,
    _request_hash,
    _store_idempotency,
    _validate_idempotency_key,
)
from audio_review_state import (
    PENDING_AUDIO_STATUSES,
    latest_audio_submission,
    open_rerecord_task_once,
    rerecord_task_is_open,
    session_audio_review_summary,
)
from content_runtime import canonical_interaction
from db.models import (
    AssessmentSession,
    Attempt,
    AttemptResponse,
    AudioSubmission,
    ContentItem,
    ContentStep,
    Student,
)
from dependencies import get_current_student, get_db

router = APIRouter(tags=["Activities"])
AUDIO_INTERACTIONS = {"read_aloud", "timed_read_aloud"}


class ActivityRuntimeSubmitRequest(BaseModel):
    step_id: int
    selected_option_ids: list[int] = Field(default_factory=list, max_length=20)
    hint_used: bool = False
    elapsed_seconds: int = Field(default=0, ge=0, le=3600)
    # Compatibility input only. Novel skip evidence is rejected below.
    declared_media_gap_skip: bool = False
    audio_storage_key: Optional[str] = None
    audio_file_size: Optional[int] = Field(default=None, gt=0)
    audio_mime_type: Optional[str] = None
    audio_duration_seconds: Optional[Decimal] = Field(default=None, ge=0)


def effective_step_state(db: Session, attempt: Attempt, step: ContentStep) -> dict[str, Any]:
    """Return fail-closed academic state plus explicit rerecord navigation state."""
    response = (
        db.query(AttemptResponse)
        .filter(
            AttemptResponse.attempt_id == attempt.id,
            AttemptResponse.step_id == step.id,
        )
        .order_by(AttemptResponse.id.desc())
        .first()
    )
    audio = latest_audio_submission(db, response)
    if audio is None:
        state = stage2_step_state(db, attempt, step)
        state.setdefault("awaiting_audio_review", False)
        state.setdefault("audio_review_status", None)
        state.setdefault("rerecord_opened", False)
        return state

    base = {
        "attempts_used": 1,
        "reinforcement_verification": False,
        "reinforcement_cycle_id": None,
        "audio_review_status": audio.status,
        "rerecord_opened": False,
    }
    if audio.status in PENDING_AUDIO_STATUSES:
        return {
            **base,
            "done": False,
            "last_correct": None,
            "awaiting_audio_review": True,
        }
    if audio.status == "rerecord_required":
        return {
            **base,
            "done": False,
            "last_correct": None,
            "awaiting_audio_review": False,
            "rerecord_opened": rerecord_task_is_open(
                db,
                student_id=_student_id_for_attempt(db, attempt),
                submission_id=audio.id,
            ),
        }
    if audio.status == "graded":
        return {
            **base,
            "done": True,
            "last_correct": response.is_correct,
            "awaiting_audio_review": False,
        }

    # Unknown review states fail closed academically and are never navigation evidence.
    return {
        **base,
        "done": False,
        "last_correct": None,
        "awaiting_audio_review": True,
    }


def _student_id_for_attempt(db: Session, attempt: Attempt) -> int:
    student_id = (
        db.query(AssessmentSession.student_id)
        .filter(AssessmentSession.id == attempt.session_id)
        .scalar()
    )
    if student_id is None:
        raise HTTPException(status_code=409, detail="تعذر تحديد صاحب محاولة النشاط")
    return int(student_id)


def _runtime_step_payload(
    db: Session,
    item: ContentItem,
    attempt: Attempt,
    step: ContentStep,
) -> dict[str, Any]:
    payload = stage2_step_payload(db, item, attempt, step)
    state = effective_step_state(db, attempt, step)
    summary = session_audio_review_summary(db, attempt.session_id)
    rerecord_actionable = (
        state.get("audio_review_status") != "rerecord_required"
        or bool(state.get("rerecord_opened"))
    )
    payload["attempts_used"] = state["attempts_used"]
    payload["retry"] = (
        state["attempts_used"] > 0
        and not state["done"]
        and not state.get("awaiting_audio_review")
        and rerecord_actionable
    )
    payload["hint_available"] = payload["retry"]
    payload["audio_review_status"] = state.get("audio_review_status")
    payload["awaiting_audio_review"] = bool(state.get("awaiting_audio_review"))
    payload["rerecord_opened"] = bool(state.get("rerecord_opened"))
    payload["pending_audio_reviews"] = summary.pending_count
    payload["rerecord_required_count"] = summary.rerecord_required_count
    return payload


def _finalize_attempt_if_done(db: Session, attempt: Attempt, item: ContentItem) -> bool:
    """Finalize only from academically completed evidence; pending review never qualifies."""
    for step in item.steps:
        if not effective_step_state(db, attempt, step)["done"]:
            return False
    if attempt.status != "completed":
        attempt.status = "completed"
        attempt.completed_at = datetime.now(timezone.utc)
    return True


def _in_progress_attempts(db: Session, session_id: int) -> list[Attempt]:
    return (
        db.query(Attempt)
        .filter(
            Attempt.session_id == session_id,
            Attempt.status == "in_progress",
        )
        .order_by(Attempt.id)
        .all()
    )


def navigation_target(
    db: Session,
    session_id: int,
    *,
    finalize_completed: bool = False,
) -> tuple[Attempt | None, ContentItem | None, ContentStep | None, int, bool]:
    """Resolve learner action independently from the audio-review aggregate.

    Returns ``(attempt, item, step, pending_review_count, finalized_any)``.
    The aggregate is computed once from latest AudioSubmission state for the
    whole session, so an actionable sibling never hides a pending review.
    """
    pending_review_count = session_audio_review_summary(db, session_id).pending_count
    finalized_any = False

    for attempt in _in_progress_attempts(db, session_id):
        item = _load_item(db, attempt.item_id)
        if item is None:
            raise HTTPException(status_code=409, detail="تعذر تحميل محتوى النشاط")

        actionable_step: ContentStep | None = None
        all_done = True

        for step in sorted(item.steps, key=lambda value: value.order_index):
            state = effective_step_state(db, attempt, step)
            if state["done"]:
                continue
            all_done = False
            if state.get("awaiting_audio_review"):
                continue
            if (
                state.get("audio_review_status") == "rerecord_required"
                and not state.get("rerecord_opened")
            ):
                continue
            actionable_step = step
            break

        if actionable_step is not None:
            return (
                attempt,
                item,
                actionable_step,
                pending_review_count,
                finalized_any,
            )

        if all_done:
            if finalize_completed:
                finalized_any = _finalize_attempt_if_done(db, attempt, item) or finalized_any
            continue

    return None, None, None, pending_review_count, finalized_any


def _attempted_item_ids(db: Session, session_id: int) -> set[int]:
    """Every attempted item is reserved for this session, including pending review."""
    return {
        int(row[0])
        for row in db.query(Attempt.item_id)
        .filter(Attempt.session_id == session_id)
        .all()
    }


def _next_unattempted_core_item(
    db: Session,
    *,
    student_id: int,
    session_id: int,
    level_id: int,
) -> ContentItem | None:
    """Choose the next approved Core item without reselecting unresolved work."""
    attempted_ids = _attempted_item_ids(db, session_id)
    query = _rich_item_query(db).filter(
        ContentItem.kind == "core_activity",
        ContentItem.level_id == level_id,
        ContentItem.status == "approved",
    )
    if attempted_ids:
        query = query.filter(ContentItem.id.notin_(attempted_ids))

    target_skill_id = _preferred_core_skill_id(
        db,
        student_id=student_id,
        session_id=session_id,
        level_id=level_id,
    )
    if target_skill_id is not None:
        preferred = (
            query.filter(ContentItem.skill_id == target_skill_id)
            .order_by(ContentItem.order_index, ContentItem.id)
            .first()
        )
        if preferred is not None:
            return preferred

    return query.order_by(ContentItem.order_index, ContentItem.id).first()


def _create_attempt(db: Session, session_id: int, item: ContentItem) -> Attempt:
    attempt = Attempt(session_id=session_id, item_id=item.id, status="in_progress")
    db.add(attempt)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        attempt = (
            db.query(Attempt)
            .filter(
                Attempt.session_id == session_id,
                Attempt.item_id == item.id,
            )
            .one()
        )
    return attempt


def _waiting_review_payload(session: AssessmentSession, level_id: int, pending_count: int) -> dict[str, Any]:
    return {
        "navigation_state": "awaiting_audio_review",
        "session_id": session.id,
        "level_id": level_id,
        "pending_audio_reviews": pending_count,
        "message": "أكملت الأنشطة المتاحة حاليًا، وتوجد تسجيلات تنتظر مراجعة المشرف.",
    }


def _rerecord_available_payload(session: AssessmentSession, level_id: int, count: int) -> dict[str, Any]:
    return {
        "navigation_state": "rerecord_available",
        "session_id": session.id,
        "level_id": level_id,
        "rerecord_required_count": count,
        "message": "لديك مهمة إعادة تسجيل جاهزة. افتحها من مسارك عندما تكون مستعدًا.",
    }


def _deferred_rerecord_tasks(
    db: Session,
    *,
    session_id: int,
    student_id: int,
) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for attempt in _in_progress_attempts(db, session_id):
        item = _load_item(db, attempt.item_id)
        if item is None:
            continue
        for step in sorted(item.steps, key=lambda value: value.order_index):
            response = (
                db.query(AttemptResponse)
                .filter(
                    AttemptResponse.attempt_id == attempt.id,
                    AttemptResponse.step_id == step.id,
                )
                .order_by(AttemptResponse.id.desc())
                .first()
            )
            submission = latest_audio_submission(db, response)
            if submission is None or submission.status != "rerecord_required":
                continue
            if rerecord_task_is_open(
                db,
                student_id=student_id,
                submission_id=submission.id,
            ):
                continue
            data = item.template_data or {}
            tasks.append({
                "submission_id": submission.id,
                "session_id": session_id,
                "attempt_id": attempt.id,
                "item_id": item.id,
                "step_id": step.id,
                "stable_key": item.stable_key,
                "title": data.get("title") or "إعادة تسجيل القراءة",
                "expected_reading_text": step.expected_reading_text,
            })
    return tasks


def _validate_learning_audio(
    *,
    student: Student,
    body: ActivityRuntimeSubmitRequest,
) -> None:
    if body.selected_option_ids:
        raise HTTPException(status_code=400, detail="جولة القراءة الجهرية تستقبل تسجيلًا صوتيًا فقط")
    if not body.audio_storage_key:
        raise HTTPException(status_code=400, detail="التسجيل الصوتي مطلوب قبل إرسال الجولة")
    if not body.audio_storage_key.startswith(f"audio/{student.id}/"):
        raise HTTPException(status_code=400, detail="مسار التسجيل الصوتي غير صالح")
    if body.audio_file_size is None or body.audio_file_size <= 0:
        raise HTTPException(status_code=400, detail="حجم التسجيل الصوتي غير صالح")
    if not body.audio_mime_type or not body.audio_mime_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="نوع التسجيل الصوتي غير صالح")
    try:
        storage.verify_audio(
            body.audio_storage_key,
            expected_size=body.audio_file_size,
            expected_content_type=body.audio_mime_type,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail="تعذر التحقق من التسجيل الصوتي المحفوظ") from exc


def _submit_learning_audio(
    *,
    session: AssessmentSession,
    item_id: int,
    body: ActivityRuntimeSubmitRequest,
    idempotency_key: str,
    db: Session,
    student: Student,
) -> dict[str, Any]:
    _validate_idempotency_key(idempotency_key)
    payload_hash = _request_hash(body.model_dump(mode="json"))
    operation = f"activity_audio_submit:{session.id}:{item_id}:{body.step_id}"
    replay = _idempotency_replay(db, student.id, operation, idempotency_key, payload_hash)
    if replay is not None:
        return replay

    attempt = (
        db.query(Attempt)
        .filter(
            Attempt.session_id == session.id,
            Attempt.item_id == item_id,
            Attempt.status == "in_progress",
        )
        .first()
    )
    if attempt is None:
        raise HTTPException(status_code=404, detail="محاولة النشاط غير موجودة أو انتهت")

    item = _load_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="النشاط غير موجود")
    if canonical_interaction(item) not in AUDIO_INTERACTIONS:
        raise HTTPException(status_code=400, detail="هذه الجولة لا تستقبل تسجيلًا صوتيًا")

    step = next((candidate for candidate in item.steps if candidate.id == body.step_id), None)
    if step is None:
        raise HTTPException(status_code=400, detail="الجولة لا تنتمي إلى هذا النشاط")

    _validate_learning_audio(student=student, body=body)

    response = (
        db.query(AttemptResponse)
        .filter(
            AttemptResponse.attempt_id == attempt.id,
            AttemptResponse.step_id == step.id,
        )
        .order_by(AttemptResponse.id.desc())
        .first()
    )
    audio = latest_audio_submission(db, response)

    if response is not None:
        if audio is None:
            raise HTTPException(status_code=409, detail="حالة التسجيل الحالية غير مكتملة. تواصل مع المشرف")
        if audio.status in PENDING_AUDIO_STATUSES:
            raise HTTPException(status_code=409, detail="التسجيل محفوظ وينتظر مراجعة المشرف")
        if audio.status == "graded":
            raise HTTPException(status_code=409, detail="تمت مراجعة هذا التسجيل مسبقًا")
        if audio.status != "rerecord_required":
            raise HTTPException(status_code=409, detail="حالة التسجيل الحالية لا تسمح بإعادة الإرسال")
        if not rerecord_task_is_open(
            db,
            student_id=student.id,
            submission_id=audio.id,
        ):
            raise HTTPException(status_code=409, detail="افتح مهمة إعادة التسجيل من مسارك أولًا")

        # Preserve the invalid submission as immutable history and append a new one.
        response.is_correct = None
        response.elapsed_seconds = body.elapsed_seconds
        db.add(AudioSubmission(
            response_id=response.id,
            storage_key=body.audio_storage_key,
            file_size=body.audio_file_size,
            mime_type=body.audio_mime_type,
            duration_seconds=body.audio_duration_seconds,
            status="uploaded",
        ))
    else:
        response = AttemptResponse(
            attempt_id=attempt.id,
            step_id=step.id,
            selected_option_id=None,
            is_correct=None,
            elapsed_seconds=body.elapsed_seconds,
        )
        db.add(response)
        db.flush()
        db.add(AudioSubmission(
            response_id=response.id,
            storage_key=body.audio_storage_key,
            file_size=body.audio_file_size,
            mime_type=body.audio_mime_type,
            duration_seconds=body.audio_duration_seconds,
            status="uploaded",
        ))

    attempt.elapsed_seconds = int(attempt.elapsed_seconds or 0) + body.elapsed_seconds
    session.elapsed_seconds = int(session.elapsed_seconds or 0) + body.elapsed_seconds
    session.updated_at = datetime.now(timezone.utc)

    result: dict[str, Any] = {
        "status": "ok",
        "is_correct": None,
        "step_complete": False,
        "activity_complete": False,
        "learning_complete": False,
        "awaiting_review": True,
        "audio_review_status": "uploaded",
        "navigation_complete": True,
    }
    _store_idempotency(db, student.id, operation, idempotency_key, payload_hash, result)
    return _commit_idempotent(db, student.id, operation, idempotency_key, payload_hash, result)


@router.get("/activities/status")
def learning_status(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    return stage2_learning_status(db=db, student=student)


@router.post("/activities/start")
def start_learning(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    return stage2_start_learning(db=db, student=student)


@router.get("/activities/session/{session_id}/progress")
def learning_progress(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = _resolve_active_session(
        db,
        requested_session_id=session_id,
        student_id=student.id,
    )
    payload = _progress_payload(db, session, session.assigned_level or student.current_level)
    summary = session_audio_review_summary(db, session.id)
    payload["pending_audio_reviews"] = summary.pending_count
    payload["rerecord_required_count"] = summary.rerecord_required_count
    return payload


@router.get("/activities/session/{session_id}/rerecord-tasks")
def rerecord_tasks(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = _resolve_active_session(
        db,
        requested_session_id=session_id,
        student_id=student.id,
    )
    return _deferred_rerecord_tasks(
        db,
        session_id=session.id,
        student_id=student.id,
    )


@router.post("/activities/session/{session_id}/attempt/{item_id}/step/{step_id}/rerecord/start")
def start_rerecord_task(
    session_id: int,
    item_id: int,
    step_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = _resolve_active_session(
        db,
        requested_session_id=session_id,
        student_id=student.id,
    )
    attempt = db.query(Attempt).filter(
        Attempt.session_id == session.id,
        Attempt.item_id == item_id,
        Attempt.status == "in_progress",
    ).first()
    if attempt is None:
        raise HTTPException(status_code=404, detail="مهمة إعادة التسجيل غير موجودة")
    item = _load_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="النشاط غير موجود")
    step = next((candidate for candidate in item.steps if candidate.id == step_id), None)
    if step is None:
        raise HTTPException(status_code=404, detail="جولة القراءة غير موجودة")
    response = db.query(AttemptResponse).filter(
        AttemptResponse.attempt_id == attempt.id,
        AttemptResponse.step_id == step.id,
    ).order_by(AttemptResponse.id.desc()).first()
    submission = latest_audio_submission(db, response)
    if submission is None or submission.status != "rerecord_required":
        raise HTTPException(status_code=409, detail="هذه الجولة لا تنتظر إعادة تسجيل")

    opened = open_rerecord_task_once(
        db,
        student_id=student.id,
        submission=submission,
        details=f"session={session.id};item={item.id};step={step.id}",
    )
    if opened:
        db.commit()
    return {
        "status": "ok",
        "opened": True,
        "session_id": session.id,
        "item_id": item.id,
        "step_id": step.id,
        "submission_id": submission.id,
    }


def _unresolved_navigation_payload(
    db: Session,
    *,
    session: AssessmentSession,
    student: Student,
    level_id: int,
) -> dict[str, Any] | None:
    summary = session_audio_review_summary(db, session.id)
    if not summary.has_unresolved:
        return None
    item = _next_unattempted_core_item(
        db,
        student_id=student.id,
        session_id=session.id,
        level_id=level_id,
    )
    if item is not None:
        attempt = _create_attempt(db, session.id, item)
        first_step = next(iter(item.steps), None)
        if first_step is None:
            raise HTTPException(status_code=409, detail="النشاط لا يحتوي على جولات معتمدة")
        return _runtime_step_payload(db, item, attempt, first_step)
    if summary.pending_count:
        return _waiting_review_payload(session, level_id, summary.pending_count)
    if summary.rerecord_required_count:
        return _rerecord_available_payload(session, level_id, summary.rerecord_required_count)
    return None


@router.get("/activities/session/{session_id}/next")
def next_activity_step(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = _resolve_active_session(
        db,
        requested_session_id=session_id,
        student_id=student.id,
    )

    attempt, item, step, _, finalized_any = navigation_target(
        db,
        session.id,
        finalize_completed=True,
    )
    if finalized_any:
        db.commit()
    if attempt is not None and item is not None and step is not None:
        return _runtime_step_payload(db, item, attempt, step)

    db.refresh(session)
    db.refresh(student)
    level_id = session.assigned_level or student.current_level

    # Academic adaptation must still evaluate already graded evidence while
    # another recording is unresolved. The adaptation bridge itself holds only
    # irreversible promotion/level-completion boundaries.
    prepared = prepare_next_for_student(db, student, session)
    if prepared.get("mapping_blocked"):
        raise HTTPException(
            status_code=409,
            detail="يحتاج المسار إلى ربط نشاط تقوية معتمد للمهارة الأضعف قبل المتابعة.",
        )
    if prepared.get("verification_escalated"):
        raise HTTPException(
            status_code=409,
            detail="يحتاج هذا الضعف إلى مراجعة المشرف بعد محاولات التقوية والتحقق.",
        )
    if prepared.get("journey_completed"):
        return None

    prepared_session_id = int(prepared.get("session_id") or session.id)
    if prepared_session_id != session.id:
        session = _activity_session_or_404(db, prepared_session_id, student.id)

    db.refresh(session)
    db.refresh(student)
    level_id = session.assigned_level or student.current_level

    attempt, item, step, _, finalized_any = navigation_target(
        db,
        session.id,
        finalize_completed=True,
    )
    if finalized_any:
        db.commit()
    if attempt is not None and item is not None and step is not None:
        return _runtime_step_payload(db, item, attempt, step)

    unresolved_payload = _unresolved_navigation_payload(
        db,
        session=session,
        student=student,
        level_id=level_id,
    )
    if unresolved_payload is not None:
        return unresolved_payload

    item = _next_unattempted_core_item(
        db,
        student_id=student.id,
        session_id=session.id,
        level_id=level_id,
    )
    if item is None:
        _finalize_session_if_done(db, session, level_id)
        db.commit()
        if session.status == "completed":
            return None
        raise HTTPException(status_code=409, detail="لا يمكن متابعة المسار دون محتوى معتمد مطابق")

    attempt = _create_attempt(db, session.id, item)
    first_step = next(iter(item.steps), None)
    if first_step is None:
        raise HTTPException(status_code=409, detail="النشاط لا يحتوي على جولات معتمدة")
    return _runtime_step_payload(db, item, attempt, first_step)


@router.post("/activities/session/{session_id}/attempt/{item_id}/submit")
def submit_activity_step(
    session_id: int,
    item_id: int,
    body: ActivityRuntimeSubmitRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = _resolve_active_session(
        db,
        requested_session_id=session_id,
        student_id=student.id,
    )

    if body.declared_media_gap_skip:
        raise HTTPException(
            status_code=409,
            detail="لا يمكن تجاوز أصل تعليمي مطلوب أو احتساب الجولة دون دليل فعلي",
        )

    item = _load_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="النشاط غير موجود")
    interaction = canonical_interaction(item)

    if interaction in AUDIO_INTERACTIONS:
        return _submit_learning_audio(
            session=session,
            item_id=item_id,
            body=body,
            idempotency_key=idempotency_key,
            db=db,
            student=student,
        )

    if any(
        [
            body.audio_storage_key,
            body.audio_file_size,
            body.audio_mime_type,
            body.audio_duration_seconds is not None,
        ]
    ):
        raise HTTPException(status_code=400, detail="هذه الجولة لا تستقبل تسجيلًا صوتيًا")

    stage2_body = ActivitySubmitRequest(
        step_id=body.step_id,
        selected_option_ids=body.selected_option_ids,
        hint_used=body.hint_used,
        elapsed_seconds=body.elapsed_seconds,
        declared_media_gap_skip=False,
    )
    return stage2_submit_activity_step(
        session_id=session.id,
        item_id=item_id,
        body=stage2_body,
        idempotency_key=idempotency_key,
        db=db,
        student=student,
    )