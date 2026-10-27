"""P03 lesson shell: resumable intro/video state without P04 scoring."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import mimetypes
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.learning_models import LessonProgressEvent, LessonSession, PlacementDecisionV2, StudentJourney
from db.models import AssessmentSession, ContentRelease, Student, User
from dependencies import get_current_student, get_current_user, get_db
from runtime_flags import protected_runtime, trial_v2_preview_allowed
from v2_content.importer import register_candidate_release
from v2_content.media import APPROVED_STATES, MISSING_STATES, MediaProvider
from v2_content.readiness import media_readiness_contract
from v2_content.projection import student_lesson
from v2_content.repository import get_lesson, get_media, get_release


router = APIRouter(prefix="/v2/lessons", tags=["v2-lessons"])
FIXTURE_VIDEO = Path(__file__).resolve().parent / "test_fixtures" / "himma-v2-video-test-only.mp4"
FIXTURE_CAPTIONS = Path(__file__).resolve().parent / "test_fixtures" / "himma-v2-video-test-only.vtt"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_LESSON_VIDEO = REPO_ROOT / "assets/video/HIMMA_V2_DEMO/gemini_generated_video_72256b30.mp4"
NEW_V2_AUDIO_ROOT = REPO_ROOT / "assets/audio/HIMMA_AUDIO_V2/web_mp3"
PREVIEW_BINDINGS_FILE = REPO_ROOT / "services/api/test_fixtures/v2-preview-bindings.json"
FALLBACK_AUDIO = REPO_ROOT / "assets/audio/HIMMA_AUDIO_V1/web_mp3/LET-01.mp3"
FALLBACK_IMAGE = REPO_ROOT / "assets/education/generated_vocabulary/webp/hem-gen-voc-001-house-512.webp"
EXTERNAL_STAGE = {"video": "teaching_video", "complete": "outcome"}


class LessonEventRequest(BaseModel):
    event_key: str = Field(min_length=8, max_length=100, pattern=r"^[A-Za-z0-9._:-]+$")
    event_type: Literal["intro_complete", "video_progress", "video_ended"]
    position_seconds: float | None = Field(default=None, ge=0, le=86400)
    duration_seconds: float | None = Field(default=None, gt=0, le=86400)


def _require_preview_student(student: Student = Depends(get_current_student)) -> Student:
    if protected_runtime() and not trial_v2_preview_allowed():
        raise HTTPException(status_code=503, detail="معاينة دروس الإصدار الثاني غير متاحة للطلاب في هذه البيئة")
    return student


def _lesson_or_404(lesson_id: str) -> dict:
    lesson = get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="الدرس غير موجود")
    return lesson


def _session_or_404(db: Session, session_id: int, student_id: int) -> LessonSession:
    session = db.query(LessonSession).filter(
        LessonSession.id == session_id,
        LessonSession.student_id == student_id,
    ).one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="جلسة الدرس غير موجودة")
    return session


def _session_payload(session: LessonSession) -> dict:
    lesson = _lesson_or_404(session.lesson_id)
    asset = get_media(lesson["video_media_id"])
    if not asset:
        raise HTTPException(status_code=409, detail="وسيط الدرس غير مسجل")
    payload = student_lesson(lesson, MediaProvider().resolve(asset).as_dict())
    payload["session"] = {
        "session_id": session.id,
        "stage": EXTERNAL_STAGE.get(session.stage, session.stage),
        "step_index": session.step_index,
        "status": session.status,
        "intro_seen": session.intro_seen,
        "video_seen": session.video_seen,
        "video_position_seconds": session.video_position_seconds,
        "video_duration_seconds": session.video_duration_seconds,
        "version": session.version,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
    }
    return payload


def _has_official_v2_placement(db: Session, student_id: int, journey: StudentJourney | None) -> bool:
    """Fail closed when a V2 lesson lacks an official, release-aligned pretest."""
    if not journey or journey.status != "active" or journey.placement_state != "placed":
        return False
    return db.query(PlacementDecisionV2.id).join(
        AssessmentSession, AssessmentSession.id == PlacementDecisionV2.assessment_session_id,
    ).filter(
        PlacementDecisionV2.student_id == student_id,
        PlacementDecisionV2.content_release_id == journey.content_release_id,
        PlacementDecisionV2.assigned_level <= journey.current_level,
        AssessmentSession.student_id == student_id,
        AssessmentSession.content_release_id == journey.content_release_id,
        AssessmentSession.session_type == "pretest",
        AssessmentSession.status == "completed",
        AssessmentSession.v2_state == "completed",
        AssessmentSession.official_for_reporting.is_(True),
        AssessmentSession.assigned_level == PlacementDecisionV2.assigned_level,
    ).first() is not None


@router.get("/catalog")
def lesson_catalog(
    student: Student = Depends(_require_preview_student),
    db: Session = Depends(get_db),
):
    release = get_release()
    active = db.query(LessonSession).filter(
        LessonSession.student_id == student.id,
        LessonSession.status.in_(("in_progress", "waiting_review")),
    ).one_or_none()
    completed = {
        row.lesson_id
        for row in db.query(LessonSession).filter(
            LessonSession.student_id == student.id,
            LessonSession.status == "completed",
        )
    }
    journey = db.query(StudentJourney).filter(StudentJourney.student_id == student.id).one_or_none()
    placed = _has_official_v2_placement(db, student.id, journey)
    # Legacy Student.current_level is never an authorization or fallback.
    current_level = journey.current_level if placed else 1
    first_for_level = next(
        row["id"] for row in release["lessons"] if int(row["level"][1]) == current_level
    )
    current_lesson_id = (
        (active.lesson_id if active else (journey.current_lesson_id or first_for_level))
        if placed else None
    )
    rows = []
    for lesson in release["lessons"]:
        if lesson["id"] in completed:
            state = "done"
        elif placed and current_lesson_id == lesson["id"]:
            state = "current"
        elif placed and int(lesson["level"][1]) < current_level:
            state = "skipped"
        else:
            state = "locked"
        rows.append({
            "lesson_id": lesson["id"],
            "title": lesson["title"],
            "level": lesson["level"],
            "state": state,
            "preview_enabled": state == "current",
            "session_id": active.id if active and active.lesson_id == lesson["id"] else None,
        })
    return {
        "mode": "candidate_preview",
        "test_only": True,
        "release_version": release["version"],
        "current_action": "lesson" if placed else "placement_required",
        "lessons": rows,
    }


@router.post("/{lesson_id}/start")
def start_lesson(
    lesson_id: str,
    student: Student = Depends(_require_preview_student),
    db: Session = Depends(get_db),
):
    # Serialize lesson starts and never create V2 academic state from V1 level.
    db.query(Student.id).filter(Student.id == student.id).with_for_update().first()
    journey = db.query(StudentJourney).filter(StudentJourney.student_id == student.id).one_or_none()
    if not _has_official_v2_placement(db, student.id, journey):
        raise HTTPException(status_code=409, detail="يجب إكمال الاختبار القبلي واعتماد التسكين أولًا")
    _lesson_or_404(lesson_id)
    active = db.query(LessonSession).filter(
        LessonSession.student_id == student.id,
        LessonSession.status.in_(("in_progress", "waiting_review")),
    ).one_or_none()
    if active:
        if active.content_release_id != journey.content_release_id:
            raise HTTPException(status_code=409, detail="جلسة الدرس لا تطابق إصدار رحلة الطالب")
        if active.lesson_id != lesson_id:
            raise HTTPException(
                status_code=409,
                detail={"message": "لديك درس قيد التنفيذ؛ عد إليه أولًا", "session_id": active.id},
            )
        return _session_payload(active)

    release_row = register_candidate_release(db)
    if journey.content_release_id != release_row.id:
        raise HTTPException(status_code=409, detail="رحلة الطالب مثبتة على إصدار محتوى مختلف")
    elif journey.current_lesson_id is None and journey.placement_state == "placed":
        # An earlier, already-approved placement can have a missing cursor.
        # GET /catalog only *projects* the fallback; the authorized POST
        # persists it atomically, and never unlocks any other lesson.
        first_placed_lesson = next(
            row["id"] for row in get_release()["lessons"]
            if int(row["level"][1]) == journey.current_level
        )
        if lesson_id != first_placed_lesson:
            raise HTTPException(
                status_code=409,
                detail={"message": "هذا الدرس ما يزال مغلقًا", "current_lesson_id": first_placed_lesson},
            )
        journey.current_lesson_id = first_placed_lesson
    elif journey.current_lesson_id != lesson_id:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "هذا الدرس ما يزال مغلقًا",
                "current_lesson_id": journey.current_lesson_id,
                "posttest_ready": journey.placement_state == "posttest_ready",
            },
        )

    session = LessonSession(
        student_id=student.id,
        content_release_id=release_row.id,
        lesson_id=lesson_id,
        return_to={"path": "/student/learning-v2"},
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return _session_payload(session)


@router.get("/sessions/{session_id}")
def lesson_session(
    session_id: int,
    student: Student = Depends(_require_preview_student),
    db: Session = Depends(get_db),
):
    return _session_payload(_session_or_404(db, session_id, student.id))


@router.post("/sessions/{session_id}/events")
def record_lesson_event(
    session_id: int,
    event: LessonEventRequest,
    student: Student = Depends(_require_preview_student),
    db: Session = Depends(get_db),
):
    session = _session_or_404(db, session_id, student.id)
    existing = db.query(LessonProgressEvent).filter(
        LessonProgressEvent.lesson_session_id == session.id,
        LessonProgressEvent.event_key == event.event_key,
    ).one_or_none()
    if existing:
        return _session_payload(session)
    # A checkpoint sent while the video was still playing may arrive after
    # video_ended. It is obsolete, not a new stage transition or a reason to
    # show an error to the learner. Return the already-advanced session
    # without rewriting the saved final position, version, or event history.
    # This exception applies only to an authorized, well-formed checkpoint;
    # premature or repeated video_ended events still fail closed.
    if (
        event.event_type == "video_progress"
        and session.video_seen
        and session.stage != "video"
        and event.position_seconds is not None
        and event.duration_seconds is not None
    ):
        return _session_payload(session)
    if session.status != "in_progress":
        raise HTTPException(status_code=409, detail="جلسة الدرس ليست قيد التنفيذ")

    if event.event_type == "intro_complete":
        if session.stage != "intro":
            raise HTTPException(status_code=409, detail="تم تجاوز مقدمة الدرس بالفعل")
        session.intro_seen = True
        session.stage = "video"
    else:
        if session.stage != "video":
            raise HTTPException(status_code=409, detail="الفيديو غير متاح في مرحلة الدرس الحالية")
        if event.position_seconds is None or event.duration_seconds is None:
            raise HTTPException(status_code=422, detail="موضع الفيديو ومدته مطلوبان")
        session.video_position_seconds = min(event.position_seconds, event.duration_seconds)
        session.video_duration_seconds = event.duration_seconds
        if event.event_type == "video_ended":
            if session.video_position_seconds / event.duration_seconds < 0.9:
                raise HTTPException(status_code=409, detail="لم تكتمل مشاهدة الفيديو بعد")
            session.video_seen = True
            session.video_completed_at = datetime.now(timezone.utc)
            session.stage = "guided_practice"

    session.version += 1
    session.updated_at = datetime.now(timezone.utc)
    db.add(LessonProgressEvent(
        lesson_session_id=session.id,
        event_key=event.event_key,
        event_type=event.event_type,
        payload_json={
            "position_seconds": event.position_seconds,
            "duration_seconds": event.duration_seconds,
        },
    ))
    from v2_rewards import reconcile_rewards
    reconcile_rewards(db, student.id, lesson_session_id=session.id)
    db.commit()
    db.refresh(session)
    return _session_payload(session)



def _bound_preview_source(asset_id: str, kind: str) -> Path | None:
    """Optional allowlisted per-ID preview binding, never a student upload path.

    Change only the JSON mapping to swap media binaries in a protected preview.
    Missing explicit files fail closed rather than silently playing another
    sound/video under the requested educational asset ID.
    """
    try:
        contents = json.loads(PREVIEW_BINDINGS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="ملف إعداد المعاينة غير صالح") from exc
    if not isinstance(contents, dict) or contents.get("schema") != "himma-v2-preview-bindings/1" or contents.get("test_only") is not True or not isinstance(contents.get("bindings"), dict):
        raise HTTPException(status_code=503, detail="عقد ربط المعاينة غير مدعوم")
    entry = contents["bindings"].get(asset_id)
    if entry is None:
        return None
    if not isinstance(entry, dict) or entry.get("kind") != kind:
        raise HTTPException(status_code=503, detail="نوع وسيط المعاينة لا يطابق المعرّف")
    raw = entry.get("path")
    suffixes = {"video": {".mp4"}, "audio": {".mp3"}, "image": {".webp", ".png"}}
    if not isinstance(raw, str) or not (
        raw.startswith("assets/") or raw.startswith("services/api/test_fixtures/")
    ):
        raise HTTPException(status_code=503, detail="مسار ملف المعاينة غير مسموح")
    path = (REPO_ROOT / raw).resolve()
    allowed_roots = [(REPO_ROOT / "assets").resolve(), (REPO_ROOT / "services/api/test_fixtures").resolve()]
    if not any(root in path.parents for root in allowed_roots) or path.suffix.lower() not in suffixes[kind] or not path.is_file():
        raise HTTPException(status_code=503, detail="ملف المعاينة المحدد غير متاح")
    return path


@router.get("/test-fixtures/video/{asset_id}")
def test_video_fixture(
    asset_id: str,
    _student: Student = Depends(_require_preview_student),
):
    asset = get_media(asset_id)
    if not asset or (asset.get("kind") or asset.get("type")) != "video":
        raise HTTPException(status_code=404, detail="فيديو المعاينة غير موجود")
    # Temporary lesson preview shared by all 19 IDs; the source video IDs stay unchanged.
    video_file = _bound_preview_source(asset_id, "video") or (DEMO_LESSON_VIDEO if DEMO_LESSON_VIDEO.is_file() else FIXTURE_VIDEO)
    if not video_file.is_file():
        raise HTTPException(status_code=503, detail="فيديو المعاينة غير جاهز")
    return FileResponse(
        video_file,
        media_type="video/mp4",
        headers={"Cache-Control": "private, no-store", "X-Himma-Test-Only": "true"},
    )


@router.get("/test-fixtures/video/{asset_id}/captions")
def test_video_captions(
    asset_id: str,
    _student: Student = Depends(_require_preview_student),
):
    asset = get_media(asset_id)
    if not asset or (asset.get("kind") or asset.get("type")) != "video":
        raise HTTPException(status_code=404, detail="ترجمة فيديو المعاينة غير موجودة")
    return FileResponse(
        FIXTURE_CAPTIONS,
        media_type="text/vtt; charset=utf-8",
        headers={"Cache-Control": "private, no-store", "X-Himma-Test-Only": "true"},
    )


def _fixture_source(asset: dict, *, kind: str) -> Path:
    explicit = _bound_preview_source(str(asset.get("id") or ""), kind)
    if explicit is not None:
        return explicit
    # New recordings supplied with V2 replace the generic audio preview fallback.
    if kind == "audio":
        asset_id = str(asset.get("id") or "")
        if asset_id.startswith("AUD-") and "/" not in asset_id and "\\" not in asset_id:
            recorded = NEW_V2_AUDIO_ROOT / f"{asset_id}.mp3"
            if recorded.is_file():
                return recorded
    source = asset.get("source_path") or asset.get("path") or asset.get("v1_path")
    if source:
        allowed_suffixes = {
            "audio": {".mp3", ".wav", ".ogg", ".m4a"},
            "image": {".webp", ".png", ".jpg", ".jpeg"},
        }
        if not isinstance(source, str) or not source.startswith("assets/"):
            raise HTTPException(status_code=503, detail="مسار الوسيط التعليمي غير مسموح")
        candidate = (REPO_ROOT / source).resolve()
        assets_root = (REPO_ROOT / "assets").resolve()
        if assets_root not in candidate.parents or candidate.suffix.lower() not in allowed_suffixes[kind]:
            raise HTTPException(status_code=503, detail="صيغة أو مسار الوسيط التعليمي غير آمن")
        if candidate.is_file():
            return candidate
    return FALLBACK_AUDIO if kind == "audio" else FALLBACK_IMAGE


@router.get("/test-fixtures/audio/{asset_id}")
def test_audio_fixture(
    asset_id: str,
    _student: Student = Depends(_require_preview_student),
):
    asset = get_media(asset_id)
    if not asset or (asset.get("kind") or asset.get("type")) != "audio":
        raise HTTPException(status_code=404, detail="صوت المعاينة غير موجود")
    source = _fixture_source(asset, kind="audio")
    if not source.is_file():
        raise HTTPException(status_code=503, detail="صوت المعاينة غير جاهز")
    return FileResponse(
        source,
        media_type=mimetypes.guess_type(source.name)[0] or "audio/mpeg",
        headers={"Cache-Control": "private, no-store", "X-Himma-Test-Only": "true"},
    )


@router.get("/test-fixtures/image/{asset_id}")
def test_image_fixture(
    asset_id: str,
    _student: Student = Depends(_require_preview_student),
):
    asset = get_media(asset_id)
    if not asset or (asset.get("kind") or asset.get("type")) != "image":
        raise HTTPException(status_code=404, detail="صورة المعاينة غير موجودة")
    source = _fixture_source(asset, kind="image")
    if not source.is_file():
        raise HTTPException(status_code=503, detail="صورة المعاينة غير جاهزة")
    media_type = mimetypes.guess_type(source.name)[0] or "image/png"
    return FileResponse(
        source,
        media_type=media_type,
        headers={"Cache-Control": "private, no-store", "X-Himma-Test-Only": "true"},
    )


@router.get("/admin/media-inventory")
def media_inventory(
    _user: User = Depends(get_current_user),
):
    return media_readiness_contract(get_release(), provider=MediaProvider())


@router.get("/admin/media/{asset_id}")
def supervisor_educational_media(asset_id: str, _user: User = Depends(get_current_user)):
    """Staff educational preview only; never a child's private recording."""
    from v2_content.media import approved_asset_path
    asset = get_media(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="الوسيط غير موجود")
    resolved = MediaProvider().resolve(asset)
    if resolved.state != "ready":
        raise HTTPException(status_code=404, detail="معاينة هذا الوسيط غير متاحة")
    path = approved_asset_path(asset)
    if path is None and resolved.test_only:
        if resolved.kind == "video":
            path = _bound_preview_source(asset_id, "video") or (DEMO_LESSON_VIDEO if DEMO_LESSON_VIDEO.is_file() else FIXTURE_VIDEO)
        elif resolved.kind in {"audio", "image"}:
            path = _fixture_source(asset, kind=resolved.kind)
    if path is None or not path.is_file():
        raise HTTPException(status_code=404, detail="ملف المعاينة غير موجود")
    return FileResponse(path, media_type=mimetypes.guess_type(path.name)[0] or "application/octet-stream",
                        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff",
                                 "X-Himma-Test-Only": str(resolved.test_only).lower()})
