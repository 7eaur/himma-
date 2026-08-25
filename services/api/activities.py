"""Adaptive learning activity runtime.

The accepted Stage-2 core runner remains the durable execution base. P06 adds
50/30/20 decisions between completed activity attempts, exact skill-matched
reinforcement, and level transitions without counting reinforcement as one of
the ten approved core activities for a level.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from assessment import (
    _commit_idempotent,
    _idempotency_replay,
    _request_hash,
    _store_idempotency,
    _validate_idempotency_key,
)
from db.activity_models import ActivityStepResponse
from db.models import (
    AssessmentSession,
    Attempt,
    AttemptResponse,
    AudioSubmission,
    ContentItem,
    ContentOption,
    ContentStep,
    Student,
)
from dependencies import get_current_student, get_db

router = APIRouter(prefix="/activities", tags=["Activities"])

MAX_STEP_ATTEMPTS = 2
CORE_ACTIVITY_COUNT = 10
REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO_ROOT / "packages" / "content" / "src" / "catalog.json"


class ActivitySubmitRequest(BaseModel):
    step_id: int
    selected_option_ids: list[int] = Field(default_factory=list, max_length=20)
    hint_used: bool = False
    elapsed_seconds: int = Field(default=0, ge=0, le=3600)
    declared_media_gap_skip: bool = False


def _catalog_round_index() -> dict[tuple[str, int], dict[str, Any]]:
    try:
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("Approved activity catalog is unavailable") from exc
    index: dict[tuple[str, int], dict[str, Any]] = {}
    for item in catalog.get("items", []):
        canonical_id = item.get("canonical_id")
        for round_data in item.get("rounds", []):
            index[(canonical_id, int(round_data.get("order_index", 0)))] = round_data
    return index


_CATALOG_ROUNDS = _catalog_round_index()


def _pretest_completed(db: Session, student_id: int) -> bool:
    return db.query(AssessmentSession.id).filter(
        AssessmentSession.student_id == student_id,
        AssessmentSession.session_type == "pretest",
        AssessmentSession.status == "completed",
    ).first() is not None


def _core_session(
    db: Session,
    student_id: int,
    *,
    completed: Optional[bool] = None,
    level_id: Optional[int] = None,
):
    query = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student_id,
        AssessmentSession.session_type == "core",
    )
    if level_id is not None:
        query = query.filter(AssessmentSession.assigned_level == level_id)
    if completed is True:
        query = query.filter(AssessmentSession.status == "completed")
    elif completed is False:
        query = query.filter(AssessmentSession.status == "in_progress")
    return query.order_by(AssessmentSession.id.desc()).first()


def _activity_session_or_404(
    db: Session,
    session_id: int,
    student_id: int,
    *,
    require_active: bool = True,
) -> AssessmentSession:
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.student_id == student_id,
        AssessmentSession.session_type == "core",
    ).first()
    if not session or (require_active and session.status != "in_progress"):
        raise HTTPException(status_code=404, detail="Active learning session not found")
    return session


def _canonical_interaction(item: ContentItem) -> str:
    data = item.template_data or {}
    return data.get("canonical_interaction_type") or item.interaction_type


def _canonical_id(item: ContentItem) -> str:
    data = item.template_data or {}
    return data.get("canonical_id") or item.stable_key


def _step_gap(item: ContentItem, step: ContentStep) -> list[dict[str, Any]]:
    return list(_CATALOG_ROUNDS.get((_canonical_id(item), step.order_index), {}).get("media_gaps", []))


def _step_assets(step: ContentStep) -> list[dict[str, Any]]:
    return [
        {
            "asset_id": asset.manifest_asset_id,
            "asset_type": asset.asset_type,
            "usage": asset.usage_context,
            "url": f"/api/media/{asset.manifest_asset_id}",
        }
        for asset in step.assets
    ]


def _step_state(db: Session, attempt: Attempt, step: ContentStep) -> dict[str, Any]:
    structured = db.query(ActivityStepResponse).filter(
        ActivityStepResponse.attempt_id == attempt.id,
        ActivityStepResponse.step_id == step.id,
    ).order_by(ActivityStepResponse.attempt_no).all()
    if structured:
        latest = structured[-1]
        done = bool(latest.is_correct or len(structured) >= MAX_STEP_ATTEMPTS)
        return {
            "done": done,
            "attempts_used": len(structured),
            "last_correct": latest.is_correct,
        }

    response = db.query(AttemptResponse).filter(
        AttemptResponse.attempt_id == attempt.id,
        AttemptResponse.step_id == step.id,
    ).first()
    if response:
        audio = db.query(AudioSubmission).filter(
            AudioSubmission.response_id == response.id,
        ).first()
        if audio and audio.status == "rerecord_required":
            return {"done": False, "attempts_used": 1, "last_correct": None}
        return {"done": True, "attempts_used": 1, "last_correct": response.is_correct}

    return {"done": False, "attempts_used": 0, "last_correct": None}


def _step_payload(db: Session, item: ContentItem, attempt: Attempt, step: ContentStep) -> dict[str, Any]:
    state = _step_state(db, attempt, step)
    interaction = _canonical_interaction(item)
    return {
        "session_id": attempt.session_id,
        "item": {
            "id": item.id,
            "stable_key": item.stable_key,
            "canonical_id": _canonical_id(item),
            "title": (item.template_data or {}).get("title") or "نشاط تعليمي",
            "level_id": item.level_id,
            "order_index": item.order_index,
            "interaction_type": interaction,
            "source_method": (item.template_data or {}).get("source_method"),
            "kind": item.kind,
        },
        "step": {
            "id": step.id,
            "order_index": step.order_index,
            "prompt_text": step.prompt_text,
            "expected_reading_text": step.expected_reading_text,
            "options": [
                {"id": option.id, "text": option.text, "order_index": option.order_index}
                for option in step.options
            ],
            "assets": _step_assets(step),
            "media_gaps": _step_gap(item, step),
        },
        "attempts_used": state["attempts_used"],
        "max_attempts": MAX_STEP_ATTEMPTS,
        "retry": state["attempts_used"] > 0 and not state["done"],
        "hint_available": state["attempts_used"] > 0 and not state["done"],
    }


def _completed_core_items(db: Session, session_id: int, level_id: int) -> int:
    return (
        db.query(Attempt.id)
        .join(ContentItem, ContentItem.id == Attempt.item_id)
        .filter(
            Attempt.session_id == session_id,
            Attempt.status == "completed",
            ContentItem.kind == "core_activity",
            ContentItem.level_id == level_id,
        )
        .count()
    )


def _progress_payload(db: Session, session: AssessmentSession, level_id: int) -> dict[str, Any]:
    total = db.query(ContentItem).filter(
        ContentItem.kind == "core_activity",
        ContentItem.level_id == level_id,
    ).count()
    return {
        "session_id": session.id,
        "status": session.status,
        "level_id": level_id,
        "completed_items": _completed_core_items(db, session.id, level_id),
        "total_items": total,
        "elapsed_seconds": session.elapsed_seconds,
    }


def _finalize_attempt_if_done(db: Session, attempt: Attempt, item: ContentItem) -> None:
    for step in item.steps:
        if not _step_state(db, attempt, step)["done"]:
            return
    attempt.status = "completed"
    attempt.completed_at = datetime.now(timezone.utc)


def _finalize_session_if_done(db: Session, session: AssessmentSession, level_id: int) -> None:
    required = db.query(ContentItem).filter(
        ContentItem.kind == "core_activity",
        ContentItem.level_id == level_id,
    ).count()
    completed = _completed_core_items(db, session.id, level_id)
    if required == CORE_ACTIVITY_COUNT and completed >= required:
        session.status = "completed"
        session.completed_at = datetime.now(timezone.utc)
        session.updated_at = datetime.now(timezone.utc)


@router.get("/status")
def learning_status(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    if not _pretest_completed(db, student.id):
        return {
            "available": False,
            "reason": "pretest_required",
            "level_id": student.current_level,
            "completed_items": 0,
            "total_items": CORE_ACTIVITY_COUNT,
            "completed": False,
            "session_id": None,
        }
    session = _core_session(db, student.id)
    if not session:
        return {
            "available": True,
            "level_id": student.current_level,
            "completed_items": 0,
            "total_items": CORE_ACTIVITY_COUNT,
            "completed": False,
            "session_id": None,
        }
    level_id = session.assigned_level or student.current_level
    progress = _progress_payload(db, session, level_id)
    return {
        "available": True,
        **progress,
        "completed": session.status == "completed",
    }


@router.post("/start")
def start_learning(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    if not student.is_active:
        raise HTTPException(status_code=403, detail="Student account is inactive")
    if not _pretest_completed(db, student.id):
        raise HTTPException(status_code=409, detail="Complete the pretest before starting learning activities")

    active_any = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student.id,
        AssessmentSession.status == "in_progress",
    ).first()
    if active_any:
        if active_any.session_type == "core":
            return _progress_payload(db, active_any, active_any.assigned_level or student.current_level)
        raise HTTPException(status_code=409, detail="Resume the active assessment first")

    completed = _core_session(db, student.id, completed=True, level_id=student.current_level)
    if completed:
        return _progress_payload(db, completed, completed.assigned_level or student.current_level)

    total = db.query(ContentItem).filter(
        ContentItem.kind == "core_activity",
        ContentItem.level_id == student.current_level,
    ).count()
    if total != CORE_ACTIVITY_COUNT:
        raise HTTPException(status_code=409, detail="Approved core activity set is incomplete")

    session = AssessmentSession(
        student_id=student.id,
        session_type="core",
        status="in_progress",
        assigned_level=student.current_level,
    )
    db.add(session)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        active = _core_session(db, student.id, completed=False)
        if active:
            return _progress_payload(db, active, active.assigned_level or student.current_level)
        raise HTTPException(status_code=409, detail="Learning session lifecycle conflict")
    db.refresh(session)
    return _progress_payload(db, session, student.current_level)


@router.get("/session/{session_id}/progress")
def learning_progress(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = _activity_session_or_404(db, session_id, student.id, require_active=False)
    return _progress_payload(db, session, session.assigned_level or student.current_level)


def _pending_attempt(db: Session, session_id: int):
    return db.query(Attempt).filter(
        Attempt.session_id == session_id,
        Attempt.status == "in_progress",
    ).order_by(Attempt.id).first()


def _load_item(db: Session, item_id: int):
    return db.query(ContentItem).options(
        joinedload(ContentItem.steps).joinedload(ContentStep.options),
        joinedload(ContentItem.steps).joinedload(ContentStep.assets),
    ).filter(ContentItem.id == item_id).first()


@router.get("/session/{session_id}/next")
def next_activity_step(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = _activity_session_or_404(db, session_id, student.id)

    pending_attempt = _pending_attempt(db, session.id)
    if pending_attempt:
        item = _load_item(db, pending_attempt.item_id)
        if not item:
            raise HTTPException(status_code=409, detail="Activity content is unavailable")
        for step in item.steps:
            if not _step_state(db, pending_attempt, step)["done"]:
                return _step_payload(db, item, pending_attempt, step)
        _finalize_attempt_if_done(db, pending_attempt, item)
        db.commit()
        pending_attempt = None

    # A completed attempt is the only moment at which the moving 50/30/20
    # snapshot can advance. The preparation helper is idempotent, so reloads do
    # not duplicate decisions or recommendations.
    from adaptation_runtime import prepare_next_for_student

    prepared = prepare_next_for_student(db, student, session)
    if prepared.get("mapping_blocked"):
        raise HTTPException(
            status_code=409,
            detail="يحتاج المسار إلى ربط نشاط تقوية معتمد للمهارة الأضعف قبل المتابعة.",
        )

    db.refresh(session)
    db.refresh(student)
    level_id = session.assigned_level or student.current_level

    pending_attempt = _pending_attempt(db, session.id)
    if pending_attempt:
        item = _load_item(db, pending_attempt.item_id)
        if not item:
            raise HTTPException(status_code=409, detail="Recommended activity content is unavailable")
        first_pending = next((step for step in item.steps if not _step_state(db, pending_attempt, step)["done"]), None)
        if first_pending:
            return _step_payload(db, item, pending_attempt, first_pending)
        _finalize_attempt_if_done(db, pending_attempt, item)
        db.commit()

    completed_ids = [
        row.item_id
        for row in db.query(Attempt.item_id).filter(
            Attempt.session_id == session.id,
            Attempt.status == "completed",
        ).all()
    ]
    query = db.query(ContentItem).options(
        joinedload(ContentItem.steps).joinedload(ContentStep.options),
        joinedload(ContentItem.steps).joinedload(ContentStep.assets),
    ).filter(
        ContentItem.kind == "core_activity",
        ContentItem.level_id == level_id,
    )
    if completed_ids:
        query = query.filter(ContentItem.id.notin_(completed_ids))
    item = query.order_by(ContentItem.order_index).first()
    if not item:
        _finalize_session_if_done(db, session, level_id)
        db.commit()
        if session.status == "completed":
            return None
        raise HTTPException(status_code=409, detail="Approved adaptive path cannot continue without mapped content")

    attempt = Attempt(session_id=session.id, item_id=item.id, status="in_progress")
    db.add(attempt)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        attempt = db.query(Attempt).filter(
            Attempt.session_id == session.id,
            Attempt.item_id == item.id,
        ).one()
    first_step = next(iter(item.steps), None)
    if not first_step:
        raise HTTPException(status_code=409, detail="Activity has no approved rounds")
    return _step_payload(db, item, attempt, first_step)


def _score_submission(item: ContentItem, step: ContentStep, option_ids: list[int]) -> bool:
    ordered = sorted(step.options, key=lambda option: option.order_index)
    valid_ids = {option.id for option in ordered}
    if not option_ids or any(option_id not in valid_ids for option_id in option_ids):
        raise HTTPException(status_code=400, detail="Response contains an option outside this activity round")

    interaction = _canonical_interaction(item)
    if interaction in {"choose_one", "listen_choose_one", "choose_image", "listen_choose_image"}:
        if len(option_ids) != 1:
            raise HTTPException(status_code=400, detail="Choose exactly one option")
        correct = next((option.id for option in ordered if option.is_correct), None)
        return option_ids[0] == correct

    if interaction in {"choose_many", "listen_choose_many"}:
        if len(ordered) < 2:
            raise HTTPException(status_code=409, detail="Approved multi-select round is incomplete")
        expected = {ordered[0].id, ordered[1].id}
        return set(option_ids) == expected and len(option_ids) == len(expected)

    if interaction in {"sequence", "memory_sequence", "path_sequence", "build_word"}:
        expected = [option.id for option in ordered]
        return option_ids == expected

    raise HTTPException(status_code=400, detail=f"Unsupported activity interaction: {interaction}")


@router.post("/session/{session_id}/attempt/{item_id}/submit")
def submit_activity_step(
    session_id: int,
    item_id: int,
    body: ActivitySubmitRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    idempotency_key = _validate_idempotency_key(idempotency_key)
    session = _activity_session_or_404(db, session_id, student.id)
    operation = f"activity.answer:{session_id}:{item_id}:{body.step_id}"
    request_hash = _request_hash(body.model_dump(mode="json"))
    replay = _idempotency_replay(db, student.id, operation, idempotency_key, request_hash)
    if replay is not None:
        return replay

    attempt = db.query(Attempt).filter(
        Attempt.session_id == session.id,
        Attempt.item_id == item_id,
        Attempt.status == "in_progress",
    ).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Active activity attempt not found")

    item = _load_item(db, item_id)
    step = next((candidate for candidate in item.steps if candidate.id == body.step_id), None) if item else None
    if not item or not step:
        raise HTTPException(status_code=400, detail="Round does not belong to this activity")

    interaction = _canonical_interaction(item)
    if interaction in {"read_aloud", "timed_read_aloud"}:
        raise HTTPException(status_code=400, detail="Use the audio upload/assessment submit path for read-aloud rounds")

    previous = db.query(ActivityStepResponse).filter(
        ActivityStepResponse.attempt_id == attempt.id,
        ActivityStepResponse.step_id == step.id,
    ).order_by(ActivityStepResponse.attempt_no).all()
    if previous and (previous[-1].is_correct or len(previous) >= MAX_STEP_ATTEMPTS):
        raise HTTPException(status_code=409, detail="This round is already complete; reload to continue")

    gaps = _step_gap(item, step)
    if body.declared_media_gap_skip:
        if not gaps:
            raise HTTPException(status_code=400, detail="This round has no declared media gap")
        is_correct = True
        payload = {"declared_media_gap_skip": True, "gaps": gaps}
    else:
        is_correct = _score_submission(item, step, body.selected_option_ids)
        payload = {"selected_option_ids": body.selected_option_ids}

    response = ActivityStepResponse(
        attempt_id=attempt.id,
        step_id=step.id,
        attempt_no=len(previous) + 1,
        response_payload=payload,
        is_correct=is_correct,
        hint_used=body.hint_used,
        elapsed_seconds=body.elapsed_seconds,
    )
    db.add(response)
    attempt.elapsed_seconds += body.elapsed_seconds
    session.elapsed_seconds += body.elapsed_seconds
    session.updated_at = datetime.now(timezone.utc)
    db.flush()

    _finalize_attempt_if_done(db, attempt, item)

    attempts_used = len(previous) + 1
    complete = bool(is_correct or attempts_used >= MAX_STEP_ATTEMPTS)
    response_json = {
        "status": "ok",
        "is_correct": is_correct,
        "attempts_used": attempts_used,
        "step_complete": complete,
        "show_hint": (not is_correct and attempts_used < MAX_STEP_ATTEMPTS),
        "activity_complete": attempt.status == "completed",
        # Session completion is deliberately finalized by GET /next after P06
        # has evaluated the newly completed attempt. This keeps the old client
        # behavior (it asks for the next step) while preventing false posttest
        # unlocks before an adaptive support/transition decision.
        "learning_complete": False,
    }
    _store_idempotency(db, student.id, operation, idempotency_key, request_hash, response_json)
    return _commit_idempotent(
        db,
        student.id,
        operation,
        idempotency_key,
        request_hash,
        response_json,
    )
