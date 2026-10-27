"""Authoritative student-facing learning view payload.

Academic scoring/adaptation remains owned by the activity runtime. This endpoint
exposes only the canonical structured presentation plus current options/media.
It consumes the same learner-navigation resolver as ``/activities/.../next`` so
pending review and deferred rerecord tasks cannot make the visual experience
point at a different step than the submission runtime.

The static learner content is serialized exclusively by
``content_student_view.activity_student_content``. Researcher preview calls the
same serializer, so question wording, instructions, current options, media,
context and layout metadata cannot drift between preview and the live learner.
Legacy prompt/source text is never parsed for student rendering.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from activities import _activity_session_or_404
from activity_runtime import effective_step_state, navigation_target
from audio_review_state import session_audio_review_summary
from content_approval_contract_2026_09_08 import LEARNING_VERSION, VERSION as APPROVAL_VERSION
from content_student_view import activity_student_content
from db.models import ContentItem, Student
from dependencies import get_current_student, get_db

router = APIRouter(prefix="/learning-experience", tags=["Learning Experience"])
VERSION = LEARNING_VERSION
MAX_STEP_ATTEMPTS = 2


def _approval(item: ContentItem) -> dict:
    value = dict((item.template_data or {}).get("content_approval_2026_09_08") or {})
    if value and value.get("version") != APPROVAL_VERSION:
        return {}
    return value


def _context_intro(item: ContentItem, assets: list[dict]) -> dict | None:
    raw = _approval(item).get("context_intro")
    if not isinstance(raw, dict):
        return None
    result = dict(raw)
    asset_id = str(result.get("audio_asset_id") or result.get("image_asset_id") or "").strip()
    if asset_id:
        matched = next((asset for asset in assets if str(asset.get("asset_id") or "") == asset_id), None)
        if matched is None:
            raise HTTPException(status_code=409, detail="وسيط شاشة السياق المعتمد غير مرتبط بالنشاط")
        result["asset"] = matched
    return result


def _layout_hint(item: ContentItem) -> str | None:
    value = _approval(item).get("layout_hint")
    return str(value) if value else None


@router.get("/session/{session_id}")
def current_learning_experience(
    session_id: int,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    session = _activity_session_or_404(db, session_id, student.id, require_active=False)

    attempt, item, step, pending_count, _ = navigation_target(
        db,
        session.id,
        finalize_completed=False,
    )
    if attempt is None or item is None or step is None:
        summary = session_audio_review_summary(db, session.id)
        if summary.pending_count:
            return {
                "version": VERSION,
                "session_id": session.id,
                "navigation_state": "awaiting_audio_review",
                "pending_audio_reviews": summary.pending_count,
                "rerecord_required_count": summary.rerecord_required_count,
            }
        if summary.rerecord_required_count:
            return {
                "version": VERSION,
                "session_id": session.id,
                "navigation_state": "rerecord_available",
                "pending_audio_reviews": 0,
                "rerecord_required_count": summary.rerecord_required_count,
            }
        return None

    data = item.template_data or {}
    if data.get("learning_experience_version") != VERSION:
        raise HTTPException(status_code=409, detail="بيانات عرض النشاط تحتاج إلى تحديث")
    experience = data.get("learning_experience") or {}
    published_round = next(
        (
            value
            for value in (experience.get("rounds") or [])
            if int(value.get("round_number") or 0) == int(step.order_index)
        ),
        None,
    )
    if not published_round:
        raise HTTPException(status_code=409, detail="تعذر العثور على بيانات الجولة الحالية")

    state = effective_step_state(db, attempt, step)
    awaiting_audio_review = bool(state.get("awaiting_audio_review"))
    rerecord_actionable = (
        state.get("audio_review_status") != "rerecord_required"
        or bool(state.get("rerecord_opened"))
    )
    static = activity_student_content(item, step)
    item_view = dict(static["item"])
    step_view = dict(static["step"])
    current_assets = list(item_view.get("assets") or [])

    round_payload = {
        "round_number": int(step_view["round_number"]),
        "round_total": int(step_view["round_total"]),
        "skill": str(step_view.get("skill") or ""),
        "encouragement": str(step_view.get("encouragement") or ""),
        "hint": str(step_view.get("hint") or ""),
        "question_text": str(step_view.get("question_text") or ""),
        "instruction_text": str(step_view.get("instruction_text") or ""),
        "stimulus_text": str(step_view.get("stimulus_text") or ""),
        "stimulus": dict(step_view.get("stimulus") or {}),
    }

    return {
        "version": VERSION,
        "session_id": session.id,
        "level_id": item_view.get("level_id"),
        "item_id": item_view.get("id"),
        "stable_key": item_view.get("stable_key"),
        "kind": item_view.get("kind"),
        "interaction_type": item_view.get("interaction_type"),
        "round": round_payload,
        "retry": state["attempts_used"] > 0 and not state["done"] and not awaiting_audio_review and rerecord_actionable,
        "attempts_used": state["attempts_used"],
        "max_attempts": MAX_STEP_ATTEMPTS,
        "audio_review_status": state.get("audio_review_status"),
        "awaiting_audio_review": awaiting_audio_review,
        "rerecord_opened": bool(state.get("rerecord_opened")),
        "pending_audio_reviews": pending_count,
        "context_intro": _context_intro(item, current_assets),
        "layout_hint": item_view.get("layout_hint") or _layout_hint(item),
        "step": {
            "id": step_view["id"],
            "order_index": step_view["order_index"],
            "expected_reading_text": step_view.get("expected_reading_text"),
            "required_selection_count": int(step_view.get("required_selection_count") or 0),
            "options": list(step_view.get("options") or []),
            "assets": list(step_view.get("assets") or []),
            "media_gaps": list(step_view.get("media_gaps") or []),
        },
        "assets": current_assets,
    }
