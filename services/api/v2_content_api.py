"""Authenticated, learner-safe preview boundary for the unapproved V2 release."""

from fastapi import APIRouter, Depends, HTTPException

from dependencies import get_any_authenticated
from runtime_flags import protected_runtime, trial_v2_preview_allowed
from v2_content.media import MediaProvider
from v2_content.projection import student_manifest, student_question
from v2_content.repository import get_media, get_question, get_release


router = APIRouter(prefix="/v2/content", tags=["v2-content"])


def _require_candidate_access(auth=Depends(get_any_authenticated)):
    role, entity = auth
    if role == "student" and protected_runtime() and not trial_v2_preview_allowed():
        raise HTTPException(status_code=503, detail="محتوى الإصدار الثاني غير معتمد للطلاب بعد")
    return role, entity


@router.get("/candidate/manifest")
def candidate_manifest(_=Depends(_require_candidate_access)):
    return student_manifest(get_release())


@router.get("/candidate/questions/{question_id}")
def candidate_question(question_id: str, _=Depends(_require_candidate_access)):
    question = get_question(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="السؤال غير موجود")
    return student_question(question)


@router.get("/candidate/media/{asset_id}")
def candidate_media(asset_id: str, _=Depends(_require_candidate_access)):
    asset = get_media(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="الوسيط غير موجود")
    return MediaProvider().resolve(asset).as_dict()
