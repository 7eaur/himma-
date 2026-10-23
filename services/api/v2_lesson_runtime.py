"""P03 lesson shell: resumable intro/video state without P04 scoring."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.learning_models import LessonProgressEvent, LessonSession, StudentJourney
from db.models import ContentRelease, Student, User
from dependencies import get_current_student, get_current_user, get_db
from runtime_flags import protected_runtime, trial_v2_preview_allowed
from v2_content.importer import register_candidate_release
from v2_content.media import APPROVED_STATES, MISSING_STATES, MediaProvider
from v2_content.projection import student_lesson
from v2_content.repository import get_lesson, get_media, get_release


router = APIRouter(prefix="/v2/lessons", tags=["v2-lessons"])
FIXTURE_VIDEO = Path(__file__).resolve().parent / "test_fixtures" / "himma-v2-video-test-only.mp4"
FIXTURE_CAPTIONS = Path(__file__).resolve().parent / "test_fixtures" / "himma-v2-video-test-only.vtt"
REPO_ROOT = Path(__file__).resolve().parents[2]
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
    first_for_level = next(
        row["id"] for row in release["lessons"] if int(row["level"][1]) == student.current_level
    )
    current_lesson_id = active.lesson_id if active else (journey.current_lesson_id if journey else first_for_level)
    current_level = journey.current_level if journey else student.current_level
    rows = []
    for lesson in release["lessons"]:
        if lesson["id"] in completed:
            state = "done"
        elif current_lesson_id == lesson["id"]:
            state = "current"
        elif int(lesson["level"][1]) < current_level:
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
        "current_action": "posttest_ready" if journey and journey.placement_state == "posttest_ready" else "lesson",
        "lessons": rows,
    }


@router.post("/{lesson_id}/start")
def start_lesson(
    lesson_id: str,
    student: Student = Depends(_require_preview_student),
    db: Session = Depends(get_db),
):
    _lesson_or_404(lesson_id)
    active = db.query(LessonSession).filter(
        LessonSession.student_id == student.id,
        LessonSession.status.in_(("in_progress", "waiting_review")),
    ).one_or_none()
    if active:
        if active.lesson_id != lesson_id:
            raise HTTPException(
                status_code=409,
                detail={"message": "لديك درس قيد التنفيذ؛ عد إليه أولًا", "session_id": active.id},
            )
        return _session_payload(active)

    release_row = register_candidate_release(db)
    journey = db.query(StudentJourney).filter(StudentJourney.student_id == student.id).one_or_none()
    if journey is None:
        first_lesson = next(
            row["id"] for row in get_release()["lessons"] if int(row["level"][1]) == student.current_level
        )
        if lesson_id != first_lesson:
            raise HTTPException(
                status_code=409,
                detail={"message": "هذا الدرس ما يزال مغلقًا", "current_lesson_id": first_lesson},
            )
        journey = StudentJourney(
            student_id=student.id,
            content_release_id=release_row.id,
            current_level=student.current_level,
            current_lesson_id=lesson_id,
        )
        db.add(journey)
    elif journey.content_release_id != release_row.id:
        raise HTTPException(status_code=409, detail="رحلة الطالب مثبتة على إصدار محتوى مختلف")
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
    db.commit()
    db.refresh(session)
    return _session_payload(session)


@router.get("/test-fixtures/video/{asset_id}")
def test_video_fixture(
    asset_id: str,
    _student: Student = Depends(_require_preview_student),
):
    asset = get_media(asset_id)
    if not asset or (asset.get("kind") or asset.get("type")) != "video":
        raise HTTPException(status_code=404, detail="فيديو المعاينة غير موجود")
    if not FIXTURE_VIDEO.is_file():
        raise HTTPException(status_code=503, detail="فيديو المعاينة غير جاهز")
    return FileResponse(
        FIXTURE_VIDEO,
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
    source = asset.get("source_path") or asset.get("path") or asset.get("v1_path")
    if source:
        candidate = (REPO_ROOT / str(source)).resolve()
        if candidate.is_relative_to(REPO_ROOT) and candidate.is_file():
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
        media_type="audio/mpeg",
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
    media_type = "image/webp" if source.suffix.lower() == ".webp" else "image/png"
    return FileResponse(
        source,
        media_type=media_type,
        headers={"Cache-Control": "private, no-store", "X-Himma-Test-Only": "true"},
    )


@router.get("/admin/media-inventory")
def media_inventory(
    _user: User = Depends(get_current_user),
):
    provider = MediaProvider()
    items = []
    counts = {"ready": 0, "pending": 0, "missing": 0, "test_only": 0}
    for asset in get_release()["media"]:
        resolved = provider.resolve(asset)
        source_status = str(asset.get("status") or "missing").lower()
        source_state = "ready" if source_status in APPROVED_STATES else "missing" if source_status in MISSING_STATES else "pending"
        counts[source_state] += 1
        if resolved.test_only:
            counts["test_only"] += 1
        items.append({
            "asset_id": resolved.asset_id,
            "kind": resolved.kind,
            "state": source_state,
            "runtime_state": resolved.state,
            "test_only": resolved.test_only,
            "source_status": asset.get("status"),
        })
    return {"mode": "read_only", "release_state": get_release()["state"], "counts": counts, "items": items}
