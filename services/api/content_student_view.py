"""Shared, read-only student presentation contract.

Both live student routes and the researcher content preview consume these exact
serializers.  This prevents preview-only formatting, positional media inference,
or accidental exposure of legacy ``source_text`` / answer metadata.
"""
from __future__ import annotations

from fastapi import HTTPException

import assessment
from content_runtime import (
    active_options,
    canonical_id,
    canonical_interaction,
    instruction_text,
    item_assets,
    media_gaps,
    presentation_data,
    step_assets,
)
from db.models import ContentItem, ContentStep

SINGLE = {"choose_one", "listen_choose_one", "choose_image", "listen_choose_image"}
MULTI = {"choose_many", "listen_choose_many"}
ORDER = {"sequence", "memory_sequence", "path_sequence", "build_word"}


def _assessment_presentation(item: ContentItem) -> dict:
    data = item.template_data or {}
    key = (
        "pretest_experience"
        if item.kind == "pretest_question"
        else "posttest_experience"
        if item.kind == "posttest_question"
        else ""
    )
    value = dict(data.get(key) or {}) if key else {}
    required = {
        "version",
        "question_number",
        "section",
        "skill",
        "encouragement",
        "question_text",
        "instruction_text",
        "interaction_type",
    }
    missing = sorted(name for name in required if value.get(name) in {None, ""})
    if missing:
        raise HTTPException(
            status_code=409,
            detail=f"بيانات عرض السؤال غير مكتملة: {', '.join(missing)}",
        )
    value.setdefault("stimulus", {"kind": "none"})
    return value


def _selection_count(item: ContentItem, step: ContentStep) -> int:
    interaction = canonical_interaction(item)
    options = active_options(step)
    if interaction in SINGLE:
        return 1
    if interaction in MULTI:
        return len([option for option in options if option.is_correct])
    if interaction in ORDER:
        return len(assessment._expected_order_ids(item, step))
    return 0


def assessment_student_payload(item: ContentItem, step: ContentStep) -> dict:
    """Return the exact assessment payload shape shown to a learner."""
    presentation = _assessment_presentation(item)
    interaction = canonical_interaction(item)
    if str(presentation.get("interaction_type")) != interaction:
        raise HTTPException(status_code=409, detail="نوع التفاعل لا يطابق بيانات عرض السؤال")
    options = active_options(step)
    return {
        "id": item.id,
        "stable_key": item.stable_key,
        "canonical_id": canonical_id(item),
        "kind": item.kind,
        "interaction_type": interaction,
        "title": str(presentation.get("skill") or "مهمة تعليمية"),
        "presentation": presentation,
        "item_assets": item_assets(item),
        "steps": [
            {
                "id": step.id,
                "order_index": step.order_index,
                "expected_reading_text": step.expected_reading_text,
                "required_selection_count": _selection_count(item, step),
                "options": [
                    {
                        "id": option.id,
                        "text": option.text,
                        "order_index": option.order_index,
                    }
                    for option in options
                ],
                "assets": step_assets(item, step),
                "media_gaps": media_gaps(item, step),
            }
        ],
    }


def activity_student_content(item: ContentItem, step: ContentStep) -> dict:
    """Return the static content portion of the live learning-step payload.

    Session/attempt/retry state is intentionally not part of this function, so
    researcher preview can call it without creating progress or attempts.  The
    same result is consumed by the live learning endpoint; this is the single
    serializer for question copy, instructions, options, media and context data.
    """
    interaction = canonical_interaction(item)
    presentation = presentation_data(item, step)
    options = active_options(step)
    skill_name = item.skill.name if item.skill is not None else str((item.template_data or {}).get("canonical_skill_code") or "")
    round_total = len(item.steps)
    stimulus = dict(presentation.get("stimulus") or {})
    stimulus_text = str(
        presentation.get("stimulus_text")
        or (stimulus.get("text") if stimulus.get("kind") == "text" else "")
        or ""
    )
    return {
        "item": {
            "id": item.id,
            "stable_key": item.stable_key,
            "canonical_id": canonical_id(item),
            "title": (item.template_data or {}).get("title") or "نشاط تعليمي",
            "level_id": item.level_id,
            "order_index": item.order_index,
            "interaction_type": interaction,
            "source_method": (item.template_data or {}).get("source_method"),
            "kind": item.kind,
            "assets": item_assets(item),
            "context_intro": ((item.template_data or {}).get("content_approval_2026_09_08") or {}).get("context_intro"),
            "layout_hint": ((item.template_data or {}).get("content_approval_2026_09_08") or {}).get("layout_hint"),
        },
        "step": {
            "id": step.id,
            "order_index": step.order_index,
            "round_number": int(presentation.get("round_number") or step.order_index),
            "round_total": int(presentation.get("round_total") or round_total),
            "skill": str(presentation.get("skill") or skill_name),
            "prompt_text": step.prompt_text,
            "question_text": str(presentation.get("question_text") or step.prompt_text or ""),
            "instruction_text": instruction_text(item, step),
            "encouragement": str(presentation.get("encouragement") or ""),
            "hint": str(presentation.get("hint") or ""),
            "stimulus_text": stimulus_text,
            "stimulus": stimulus,
            "expected_reading_text": step.expected_reading_text,
            "required_selection_count": _selection_count(item, step),
            "options": [
                {
                    "id": option.id,
                    "text": option.text,
                    "order_index": option.order_index,
                }
                for option in options
            ],
            "assets": step_assets(item, step),
            "media_gaps": media_gaps(item, step),
        },
    }
