"""Authenticated, learner-safe preview boundary for the unapproved V2 release."""

from fastapi import APIRouter, Depends, HTTPException, Query
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


@router.get("/admin/bank")
def supervisor_content_bank(
    section: str = Query(default="", max_length=30), search: str = Query(default="", max_length=100),
    limit: int = Query(default=25, ge=1, le=50), offset: int = Query(default=0, ge=0),
    _user: User = Depends(get_current_user),
):
    """Read-only current authoring bank; private answers require staff authorization."""
    release = get_release()
    sections = [{"id": "pretest", "title": "الاختبار القبلي", "kind": "assessment", "intro": None}]
    for lesson in release["lessons"]:
        sections.append({"id": lesson["id"], "title": lesson["title"], "kind": "lesson",
                         "intro": lesson.get("intro"), "objective": lesson.get("objective")})
    for support in release["supports"]:
        sections.append({"id": support["id"], "title": support["title"], "kind": "support",
                         "intro": support.get("intro"), "objective": support.get("objective")})
    sections.append({"id": "posttest", "title": "الاختبار البعدي", "kind": "assessment", "intro": None})
    order = {row["id"]: i for i, row in enumerate(sections)}
    if section and section not in order:
        raise HTTPException(status_code=404, detail="قسم المحتوى غير موجود")
    questions = sorted(release["questions"], key=lambda q: (
        order[q.get("owner_id") or q["role"]],
        {"guided_practice": 0, "independent_check": 1, "support_check": 1}.get(q["role"], 0), q["id"],
    ))
    for row in sections:
        row["question_count"] = sum((q.get("owner_id") or q["role"]) == row["id"] for q in questions)
    selected = [q for q in questions if (not section or (q.get("owner_id") or q["role"]) == section)
                and (not search.strip() or search.strip().casefold() in f'{q["id"]} {q["prompt"]}'.casefold())]
    items = []
    for question in selected[offset:offset + limit]:
        media_ids = {m["media_id"] for m in question.get("stimulus", {}).get("media", [])}
        media_ids |= {m["media_id"] for option in question.get("options", []) for m in option.get("media", [])}
        media = []
        for asset in release["media"]:
            if asset["id"] in media_ids:
                resolved = MediaProvider().resolve(asset).as_dict()
                resolved["url"] = f'/api/v2/lessons/admin/media/{asset["id"]}' if resolved["state"] == "ready" else None
                media.append(resolved)
        items.append({"question": student_question(question), "section_id": question.get("owner_id") or question["role"],
                      "answer": question.get("private_answer"), "reading_reference": question.get("reading_reference"),
                      "media": media})
    return {"mode": "read_only", "release_version": release["version"], "release_checksum": release["checksum"],
            "release_state": release["state"], "bank_total": len(questions), "total": len(selected),
            "sections": sections, "items": items, "offset": offset,
            "next_offset": offset + limit if offset + limit < len(selected) else None}


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
