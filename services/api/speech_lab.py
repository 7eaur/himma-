"""Supervisor-only evaluation lab for Himma speech models.

The lab is intentionally isolated from the student academic path. It reads the
same approved PostgreSQL reading targets shown to learners, accepts an ad-hoc
supervisor recording, and returns lexical / pronunciation evidence for model
evaluation. It never creates or edits student sessions, attempts, reviews,
adaptation decisions, rewards, or scores.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session, joinedload

from arabic_pronunciation import build_pronunciation_reference
from azure_pronunciation_provider import AzurePronunciationAssessmentProvider
from content_runtime import canonical_id, canonical_interaction
from db.models import ContentItem, ContentRelease, ContentStep, User
from dependencies import get_current_user, get_db
from pronunciation_evidence import build_acoustic_evidence_plan
from speech_aliases import alias_evidence
from speech_alignment import align_reference, alignment_counts, normalize_arabic
from speech_decision import preview_speech_decision
from speech_provider import (
    ProviderNotConfigured,
    ProviderPermanentError,
    ProviderTemporaryError,
    build_evaluation_provider,
)
from speech_quality import RecordingQualityError, validate_provider_output, validate_recording_input
from speech_task_profiles import profile_for, require_profile

router = APIRouter(prefix="/admin/speech-lab", tags=["speech-lab"])

_READ_INTERACTIONS = {"read_aloud", "timed_read_aloud"}
_MAX_LAB_AUDIO_BYTES = 15 * 1024 * 1024


def _require_supervisor(user: User = Depends(get_current_user)) -> User:
    if user.role != "researcher" or not user.is_active:
        raise HTTPException(status_code=403, detail="هذه الصفحة متاحة للمشرف فقط")
    return user


def _group_for(item: ContentItem) -> str:
    if item.kind == "pretest_question":
        return "pretest"
    if item.kind == "posttest_question":
        return "posttest"
    if item.kind == "reinforcement_activity":
        return f"level_{int(item.level_id)}_reinforcement"
    return f"level_{int(item.level_id)}_core"


def _title(item: ContentItem) -> str:
    data = item.template_data or {}
    return str(data.get("title") or (item.skill.name if item.skill else "") or "مهمة قراءة")


def _targets(db: Session) -> list[dict[str, Any]]:
    items = (
        db.query(ContentItem)
        .options(
            joinedload(ContentItem.steps),
            joinedload(ContentItem.skill),
        )
        .filter(ContentItem.status == "approved")
        .order_by(ContentItem.kind, ContentItem.level_id, ContentItem.order_index, ContentItem.id)
        .all()
    )

    targets: list[dict[str, Any]] = []
    for item in items:
        interaction = canonical_interaction(item)
        if interaction not in _READ_INTERACTIONS:
            continue
        for step in sorted(item.steps, key=lambda row: (int(row.order_index), int(row.id or 0))):
            reference = str(step.expected_reading_text or "").strip()
            if not reference:
                continue
            item_canonical_id = canonical_id(item)
            profile = profile_for(item_canonical_id)
            pronunciation = build_pronunciation_reference(reference)
            targets.append(
                {
                    "target_id": f"{item_canonical_id}-R{int(step.order_index):02d}",
                    "canonical_id": item_canonical_id,
                    "title": _title(item),
                    "group": _group_for(item),
                    "kind": str(item.kind),
                    "level_id": int(item.level_id) if item.level_id is not None else None,
                    "skill_name": item.skill.name if item.skill else None,
                    "interaction_type": interaction,
                    "round_index": int(step.order_index),
                    "reference_text": reference,
                    "pronunciation_target_type": pronunciation["target_type"],
                    "has_diacritics": pronunciation["has_diacritics"],
                    "speech_mode": profile.mode if profile else "unclassified",
                    "pronunciation_focus": profile.focus if profile else None,
                    "lexical_reference": normalize_arabic(reference),
                }
            )
    return targets


def _target_for_id(db: Session, target_id: str) -> dict[str, Any]:
    wanted = (target_id or "").strip()
    if not wanted:
        raise HTTPException(status_code=422, detail="هدف القراءة مطلوب")
    target = next((row for row in _targets(db) if row["target_id"] == wanted), None)
    if target is None:
        raise HTTPException(status_code=404, detail="هدف القراءة غير موجود في المحتوى المعتمد")
    if target["speech_mode"] == "unclassified":
        raise HTTPException(
            status_code=409,
            detail="هدف القراءة الجديد يحتاج Speech Profile صريح قبل التحليل",
        )
    return target


def _active_release(db: Session) -> str | None:
    row = db.query(ContentRelease).filter(ContentRelease.is_active.is_(True)).first()
    return str(row.version) if row else None


@router.get("/targets")
def get_targets(
    db: Session = Depends(get_db),
    _: User = Depends(_require_supervisor),
):
    targets = _targets(db)
    return {
        "source": "approved_postgresql_content",
        "release_version": _active_release(db),
        "count": len(targets),
        "targets": targets,
    }


@router.get("/pronunciation-reference")
def pronunciation_reference(
    reference_text: str = Query(min_length=1),
    _: User = Depends(_require_supervisor),
):
    return build_pronunciation_reference(reference_text.strip())


@router.get("/acoustic-plan")
def acoustic_plan(
    reference_text: str = Query(min_length=1),
    _: User = Depends(_require_supervisor),
):
    return build_acoustic_evidence_plan(reference_text.strip())


@router.get("/provider")
def provider_status(_: User = Depends(_require_supervisor)):
    lexical: dict[str, Any]
    try:
        provider = build_evaluation_provider()
        if provider.name == "unconfigured":
            lexical = {"configured": False, "provider": None}
        else:
            lexical = {"configured": True, "provider": provider.name}
    except ProviderNotConfigured as exc:
        lexical = {"configured": False, "provider": None, "detail": str(exc)}

    try:
        pronunciation = AzurePronunciationAssessmentProvider()
        pronunciation_state: dict[str, Any] = {
            "configured": True,
            "provider": pronunciation.name,
            "locale": pronunciation.locale,
        }
    except ProviderPermanentError as exc:
        pronunciation_state = {
            "configured": False,
            "provider": "azure-pronunciation-assessment",
            "detail": str(exc),
        }

    return {
        "mode": "evaluation_only",
        "academic_effect": "none",
        "lexical": lexical,
        "pronunciation": pronunciation_state,
    }


def _quality_or_http(
    *,
    audio_bytes: bytes,
    mime_type: str | None,
    duration_seconds: float | None,
) -> dict[str, object]:
    try:
        return validate_recording_input(
            audio_bytes=audio_bytes,
            mime_type=mime_type,
            duration_seconds=duration_seconds,
            max_bytes=_MAX_LAB_AUDIO_BYTES,
        )
    except RecordingQualityError as exc:
        raise HTTPException(
            status_code=413 if exc.code == "audio_too_large" else 422,
            detail=exc.message,
        ) from exc


@router.post("/analyze")
async def analyze_recording(
    target_id: str = Form(...),
    reference_text: str | None = Form(default=None),
    adaptation_mode: str = Form(default="reference"),
    client_duration_seconds: float | None = Form(default=None),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(_require_supervisor),
):
    target = _target_for_id(db, target_id)
    profile = require_profile(str(target["canonical_id"]))
    reference = str(target["reference_text"]).strip()

    client_reference = (reference_text or "").strip()
    if client_reference and normalize_arabic(client_reference) != normalize_arabic(reference):
        raise HTTPException(
            status_code=409,
            detail="النص المرجعي في الصفحة لا يطابق المحتوى المعتمد؛ حدّث الصفحة ثم أعد المحاولة",
        )
    if adaptation_mode not in {"none", "reference"}:
        raise HTTPException(status_code=422, detail="وضع التكييف غير مدعوم")

    audio_bytes = await audio.read()
    input_quality = _quality_or_http(
        audio_bytes=audio_bytes,
        mime_type=audio.content_type,
        duration_seconds=client_duration_seconds,
    )

    try:
        provider = build_evaluation_provider()
        result = provider.transcribe_reference_guided(
            audio_bytes=audio_bytes,
            mime_type=audio.content_type or "application/octet-stream",
            reference_text=reference if adaptation_mode == "reference" else "",
            language="ar-OM",
        )
        output_quality = validate_provider_output(
            transcript=result.transcript,
            duration_seconds=result.duration_seconds,
        )
    except RecordingQualityError as exc:
        raise HTTPException(status_code=422, detail=exc.message) from exc
    except ProviderNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProviderTemporaryError as exc:
        raise HTTPException(status_code=503, detail=f"تعذر الوصول إلى مزود التحليل مؤقتًا: {exc}") from exc
    except ProviderPermanentError as exc:
        raise HTTPException(status_code=422, detail=f"رفض مزود التحليل التسجيل: {exc}") from exc

    aligned = align_reference(reference, result.transcript)
    counts = alignment_counts(aligned)
    aliases = (
        alias_evidence(target_id, result.transcript)
        if profile.mode == "targeted_pronunciation"
        else {"matched": False, "effect": None, "matched_alias": None}
    )
    ref_words = max(1, len(normalize_arabic(reference).split()))
    errors = counts["deletion"] + counts["insertion"] + counts["substitution"]
    wer = errors / ref_words
    decision = preview_speech_decision(
        mode=profile.mode,
        counts=counts,
        alias_matched=bool(aliases["matched"]),
    )

    return {
        "lab_only": True,
        "academic_effect": "none",
        "target_id": target_id,
        "canonical_id": target["canonical_id"],
        "speech_mode": profile.mode,
        "pronunciation_focus": profile.focus,
        "analysis_path": "lexical_alignment" if profile.mode in {"lexical", "fluency"} else "targeted_pronunciation_preview",
        "asr_alias_evidence": aliases,
        "decision_preview": {
            "state": decision.state,
            "reason": decision.reason,
            "academic_effect": "none",
        },
        "adaptation_mode": adaptation_mode,
        "provider": result.provider_name,
        "model": result.model,
        "request_id": result.request_id,
        "reference_text": reference,
        "normalized_reference": normalize_arabic(reference),
        "raw_transcript": result.transcript,
        "normalized_transcript": normalize_arabic(result.transcript),
        "provider_confidence": result.confidence,
        "duration_seconds": result.duration_seconds,
        "recording_quality": {
            "input": input_quality,
            "provider_output": output_quality,
            "rerecord_required": False,
        },
        "counts": counts,
        "wer": wer,
        "lexical_accuracy": max(0.0, 1.0 - wer),
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
        "pronunciation_reference": (
            build_pronunciation_reference(reference)
            if profile.mode == "targeted_pronunciation"
            else None
        ),
        "acoustic_evidence": (
            build_acoustic_evidence_plan(reference)
            if profile.mode == "targeted_pronunciation"
            else None
        ),
        "pronunciation_status": (
            "not_calibrated" if profile.mode == "targeted_pronunciation" else "not_applicable"
        ),
        "fluency": (
            {
                "client_duration_seconds": client_duration_seconds,
                "provider_duration_seconds": result.duration_seconds,
                "reference_word_count": ref_words,
            }
            if profile.mode == "fluency"
            else None
        ),
        "raw_metadata": result.raw_metadata,
    }


@router.post("/pronunciation-assess")
async def pronunciation_assess(
    target_id: str = Form(...),
    reference_text: str | None = Form(default=None),
    client_duration_seconds: float | None = Form(default=None),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(_require_supervisor),
):
    target = _target_for_id(db, target_id)
    profile = require_profile(str(target["canonical_id"]))
    if profile.mode != "targeted_pronunciation":
        raise HTTPException(
            status_code=409,
            detail="هذا الهدف يستخدم القراءة النصية ولا يحتاج تقييم نطق مستهدف",
        )

    reference = str(target["reference_text"]).strip()
    client_reference = (reference_text or "").strip()
    if client_reference and normalize_arabic(client_reference) != normalize_arabic(reference):
        raise HTTPException(
            status_code=409,
            detail="النص المرجعي في الصفحة لا يطابق المحتوى المعتمد؛ حدّث الصفحة ثم أعد المحاولة",
        )

    audio_bytes = await audio.read()
    input_quality = _quality_or_http(
        audio_bytes=audio_bytes,
        mime_type=audio.content_type,
        duration_seconds=client_duration_seconds,
    )

    try:
        provider = AzurePronunciationAssessmentProvider()
        result = provider.assess(
            audio_bytes=audio_bytes,
            mime_type=audio.content_type or "application/octet-stream",
            reference_text=reference,
        )
    except ProviderTemporaryError as exc:
        raise HTTPException(status_code=503, detail=f"تعذر الوصول إلى مزود النطق مؤقتًا: {exc}") from exc
    except ProviderPermanentError as exc:
        raise HTTPException(status_code=422, detail=f"تعذر تقييم التسجيل تجريبيًا: {exc}") from exc

    return {
        "lab_only": True,
        "academic_effect": "none",
        "calibration_status": "not_calibrated",
        "direct_haraka_judgement": False,
        "target_id": target_id,
        "canonical_id": target["canonical_id"],
        "speech_mode": profile.mode,
        "pronunciation_focus": profile.focus,
        "reference_text": reference,
        "recording_quality": {"input": input_quality, "rerecord_required": False},
        "provider": result.provider_name,
        "locale": result.locale,
        "transcript": result.transcript,
        "recognition_status": result.recognition_status,
        "confidence": result.confidence,
        "accuracy_score": result.accuracy_score,
        "fluency_score": result.fluency_score,
        "completeness_score": result.completeness_score,
        "pronunciation_score": result.pronunciation_score,
        "words": [
            {
                "word": word.word,
                "accuracy_score": word.accuracy_score,
                "error_type": word.error_type,
                "offset_seconds": word.offset_seconds,
                "duration_seconds": word.duration_seconds,
                "phoneme_scores": list(word.phoneme_scores),
            }
            for word in result.words
        ],
        "request_id": result.request_id,
        "raw_metadata": result.raw_metadata,
        "pronunciation_reference": build_pronunciation_reference(reference),
        "acoustic_evidence": build_acoustic_evidence_plan(reference),
    }
