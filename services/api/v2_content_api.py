"""Authenticated, learner-safe preview boundary for the unapproved V2 release."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from dependencies import get_any_authenticated, get_current_user, get_db
from sqlalchemy.orm import Session
from db.models import User
from runtime_flags import protected_runtime, trial_v2_preview_allowed
from v2_content.media import MediaProvider, approved_asset_path
from v2_content.projection import student_manifest, student_question
from v2_content.repository import get_media, get_question, get_release
from v2_content.recovery import restore_original_snapshot


router = APIRouter(prefix="/v2/content", tags=["v2-content"])


@router.post("/admin/releases/{release_id}/restore-original-snapshot")
def restore_historical_snapshot(release_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = restore_original_snapshot(db, release_id, user.id)
    db.commit()
    return result


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


@router.get("/media/{asset_id}")
def approved_media_file(asset_id: str, _=Depends(_require_candidate_access)):
    """Serve a verified approved educational asset, never a TEST_ONLY fixture."""
    asset = get_media(asset_id)
    path = approved_asset_path(asset) if asset else None
    if path is None:
        raise HTTPException(status_code=404, detail="ملف الوسيط غير معتمد أو غير موجود")
    import mimetypes
    return FileResponse(path, media_type=mimetypes.guess_type(path.name)[0] or "application/octet-stream",
                        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})
