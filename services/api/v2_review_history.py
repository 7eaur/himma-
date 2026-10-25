"""P08 supervisor-only chronological evidence for grade reviews and retries.

Never return S3 storage keys or idempotency tokens: historical audio is
played through an authenticated, owner-scoped route.
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

import recordings
from db.learning_models import V2LessonReviewAction, V2ReviewRetryTask
from db.models import AudioSubmission, User
from dependencies import get_current_user, get_db
from v2_retry_runtime import _owner

router = APIRouter(prefix="/v2/review-history", tags=["v2-review-history"])


def _timestamp(value):
    return value.isoformat() if value is not None else None


def _audio_query(db: Session, kind: Literal["lesson", "assessment"], response_id: int):
    if kind == "lesson":
        return db.query(AudioSubmission).filter(AudioSubmission.lesson_response_id == response_id)
    return db.query(AudioSubmission).filter(AudioSubmission.assessment_response_id == response_id)


def _retry_query(db: Session, kind: Literal["lesson", "assessment"], response_id: int):
    if kind == "lesson":
        return db.query(V2ReviewRetryTask).filter(V2ReviewRetryTask.lesson_response_id == response_id)
    return db.query(V2ReviewRetryTask).filter(V2ReviewRetryTask.assessment_response_id == response_id)


@router.get("/admin/{kind}/{response_id}")
def review_history(
    kind: Literal["lesson", "assessment"], response_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row, session, question = _owner(db, kind, response_id)
    original = ((row.answer_json or {}).get("answer") or {}) if kind == "lesson" else (row.answer_json or {})
    tasks = _retry_query(db, kind, response_id).order_by(V2ReviewRetryTask.id).all()
    audios = _audio_query(db, kind, response_id).order_by(AudioSubmission.id).all()
    if kind == "lesson":
        decisions = [{
            "reviewer_id": item.reviewer_id,
            "is_correct": item.is_correct,
            "note": item.note,
            "at": _timestamp(item.created_at),
        } for item in db.query(V2LessonReviewAction).filter(
            V2LessonReviewAction.lesson_response_id == response_id,
        ).order_by(V2LessonReviewAction.id).all()]
    else:
        decisions = [{
            "reviewer_id": row.reviewed_by,
            "is_correct": row.is_correct,
            "note": row.review_note,
            "at": _timestamp(row.reviewed_at),
        }] if row.reviewed_at else []
    return {
        "kind": kind,
        "response_id": response_id,
        "question_id": row.question_id,
        "interaction": question["interaction"],
        "status": row.status,
        "original": {
            "text_response": original.get("text_response") if question["interaction"] == "write_text" else None,
            "submitted_at": _timestamp(row.created_at),
        },
        "retries": [{
            "task_id": task.id,
            "kind": task.request_kind,
            "status": task.status,
            "reason": task.reason,
            "requested_at": _timestamp(task.created_at),
            "submitted_at": _timestamp(task.submitted_at),
            "resolved_at": _timestamp(task.resolved_at),
            "text_response": (
                task.replacement_json.get("text_response")
                if question["interaction"] == "write_text" and isinstance(task.replacement_json, dict)
                else None
            ),
            "superseded_recording_count": len(
                (task.replacement_json or {}).get("superseded_staged_audio") or []
            ),
        } for task in tasks],
        "recordings": [{
            "id": audio.id,
            "status": audio.status,
            "file_size": audio.file_size,
            "duration_seconds": float(audio.duration_seconds) if audio.duration_seconds is not None else None,
            "submitted_at": _timestamp(audio.submitted_at),
            "url": (f"/api/v2/review-history/admin/{kind}/{response_id}/recordings/{audio.id}"
                    if audio.status not in {"purged", "retention_pending"} else None),
        } for audio in audios],
        "decisions": decisions,
    }


@router.get("/admin/{kind}/{response_id}/recordings/{audio_id}")
def review_historical_audio(
    kind: Literal["lesson", "assessment"], response_id: int, audio_id: int,
    range_header: str | None = Header(default=None, alias="Range"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row, session, question = _owner(db, kind, response_id)
    if question["interaction"] != "read_aloud":
        raise HTTPException(status_code=404, detail="لا يوجد صوت لهذا السؤال")
    audio = _audio_query(db, kind, row.id).filter(AudioSubmission.id == audio_id).one_or_none()
    if not audio or not audio.storage_key.startswith(f"audio/{session.student_id}/"):
        raise HTTPException(status_code=404, detail="تسجيل المراجعة غير موجود")
    return recordings.play_by_key(key=audio.storage_key, range_header=range_header, researcher=user)
