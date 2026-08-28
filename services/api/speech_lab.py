"""Supervisor-only speech evaluation lab for Himma.

This module deliberately stays outside the academic scoring/adaptation path.
It exposes canonical read-aloud targets and lets a supervisor run the configured
ASR provider against an ad-hoc recording, then inspect the reference-guided
alignment. Lab runs never mutate student scores, attempts, rewards, adaptation
or reinforcement evidence.
"""

from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from content_runtime import _CATALOG
from dependencies import get_current_user
from speech_alignment import align_reference, alignment_counts, normalize_arabic
from speech_provider import (
    ProviderNotConfigured,
    ProviderPermanentError,
    ProviderTemporaryError,
    build_provider,
)

router = APIRouter(prefix="/api/admin/speech-lab", tags=["speech-lab"])

_READ_INTERACTIONS = {"read_aloud", "timed_read_aloud"}
_READ_PREFIX = re.compile(r"^\s*(?:اقرأ|يقرأ|قراءة)\s*[:：]\s*", re.UNICODE)


def _require_supervisor(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    """Fail closed for non-supervisors even if they know the admin API URL."""
    if user.get("role") != "researcher":
        raise HTTPException(status_code=403, detail="غير مصرح بالوصول إلى مختبر الصوت")
    return user


def _reference_text(item: dict[str, Any], round_data: dict[str, Any]) -> str:
    """Extract the canonical text that is actually intended to be read aloud."""
    for key in ("expected_reading_text", "reference_text", "reading_text", "target_text", "text"):
        value = round_data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    source_text = str(round_data.get("source_text") or "").strip()
    if source_text:
        return _READ_PREFIX.sub("", source_text).strip()
    return ""


def _group_for(item: dict[str, Any]) -> str:
    kind = str(item.get("kind") or "")
    canonical = str(item.get("canonical_id") or "")
    if kind == "pretest_question" or canonical.startswith("PRE-"):
        return "pretest"
    if kind == "posttest_question" or canonical.startswith("POST-"):
        return "posttest"
    if "reinforcement" in kind or "-REIN-" in canonical:
        return "reinforcement"
    return f"level_{item.get('level_id') or 'unknown'}"


def canonical_reading_targets() -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for item in _CATALOG.get("items", []):
        interaction = str(item.get("interaction_type") or item.get("interaction") or "")
        if interaction not in _READ_INTERACTIONS:
            continue
        for index, round_data in enumerate(item.get("rounds") or [], start=1):
            reference_text = _reference_text(item, round_data)
            if not reference_text:
                continue
            targets.append(
                {
                    "target_id": str(round_data.get("round_id") or f"{item.get('canonical_id')}-R{index:02d}"),
                    "canonical_id": item.get("canonical_id"),
                    "title": item.get("title"),
                    "group": _group_for(item),
                    "kind": item.get("kind"),
                    "level_id": item.get("level_id"),
                    "skill_id": item.get("skill_id"),
                    "skill_name": item.get("skill_name"),
                    "interaction_type": interaction,
                    "round_index": int(round_data.get("order_index") or index),
                    "reference_text": reference_text,
                }
            )
    return targets


@router.get("/targets")
def get_targets(_: dict[str, Any] = Depends(_require_supervisor)):
    targets = canonical_reading_targets()
    return {
        "catalog_version": _CATALOG.get("catalog_version"),
        "count": len(targets),
        "targets": targets,
    }


@router.get("/provider")
def provider_status(_: dict[str, Any] = Depends(_require_supervisor)):
    try:
        provider = build_provider()
        return {"configured": provider.name != "unconfigured", "provider": provider.name}
    except ProviderNotConfigured as exc:
        return {"configured": False, "provider": None, "detail": str(exc)}


@router.post("/analyze")
async def analyze_recording(
    reference_text: str = Form(...),
    target_id: str | None = Form(default=None),
    adaptation_mode: str = Form(default="reference"),
    audio: UploadFile = File(...),
    _: dict[str, Any] = Depends(_require_supervisor),
):
    reference_text = reference_text.strip()
    if not reference_text:
        raise HTTPException(status_code=422, detail="النص المرجعي مطلوب")
    if adaptation_mode not in {"none", "reference"}:
        raise HTTPException(status_code=422, detail="وضع التكييف غير مدعوم")

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=422, detail="ملف التسجيل فارغ")
    if len(audio_bytes) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="ملف التسجيل أكبر من الحد المسموح للمختبر")

    try:
        provider = build_provider()
        result = provider.transcribe_reference_guided(
            audio_bytes=audio_bytes,
            mime_type=audio.content_type or "application/octet-stream",
            reference_text=reference_text if adaptation_mode == "reference" else "",
            language="ar-OM",
        )
    except ProviderNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProviderTemporaryError as exc:
        raise HTTPException(status_code=503, detail=f"تعذر الوصول إلى مزود التحليل مؤقتًا: {exc}") from exc
    except ProviderPermanentError as exc:
        raise HTTPException(status_code=422, detail=f"رفض مزود التحليل التسجيل: {exc}") from exc

    aligned = align_reference(reference_text, result.transcript)
    counts = alignment_counts(aligned)
    ref_words = max(1, len(normalize_arabic(reference_text).split()))
    errors = counts["deletion"] + counts["insertion"] + counts["substitution"]
    wer = errors / ref_words
    lexical_accuracy = max(0.0, 1.0 - wer)

    return {
        "lab_only": True,
        "target_id": target_id,
        "adaptation_mode": adaptation_mode,
        "provider": result.provider_name,
        "model": result.model,
        "request_id": result.request_id,
        "reference_text": reference_text,
        "normalized_reference": normalize_arabic(reference_text),
        "raw_transcript": result.transcript,
        "normalized_transcript": normalize_arabic(result.transcript),
        "provider_confidence": result.confidence,
        "duration_seconds": result.duration_seconds,
        "counts": counts,
        "wer": wer,
        "lexical_accuracy": lexical_accuracy,
        "alignment": [
            {
                "kind": token.kind,
                "reference": token.reference,
                "hypothesis": token.hypothesis,
                "reference_index": token.reference_index,
                "hypothesis_index": token.hypothesis_index,
            }
            for token in aligned
        ],
        "words": [
            {
                "text": word.text,
                "start_seconds": word.start_seconds,
                "end_seconds": word.end_seconds,
                "confidence": word.confidence,
            }
            for word in result.words
        ],
        "raw_metadata": result.raw_metadata,
        "academic_effect": "none",
        "pronunciation_status": "not_calibrated",
    }
