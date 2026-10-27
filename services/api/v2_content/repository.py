"""Read-only repository for the deterministic V2 candidate release."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from .compiler import compile_release


@lru_cache(maxsize=1)
def get_release() -> dict[str, Any]:
    return compile_release()


def get_question(question_id: str) -> dict[str, Any] | None:
    return next((row for row in get_release()["questions"] if row["id"] == question_id), None)


def get_media(asset_id: str) -> dict[str, Any] | None:
    return next((row for row in get_release()["media"] if row["id"] == asset_id), None)


def get_lesson(lesson_id: str) -> dict[str, Any] | None:
    return next((row for row in get_release()["lessons"] if row["id"] == lesson_id), None)


def get_support(support_id: str) -> dict[str, Any] | None:
    return next((row for row in get_release()["supports"] if row["id"] == support_id), None)


def get_support_for_lesson(lesson_id: str) -> dict[str, Any] | None:
    """Resolve support from either the lesson shortcut or reverse links.

    L1 authoring rows contain ``linked_support`` while later levels rely on
    ``SupportDefinition.linked_lessons``. Keeping resolution here prevents
    runtime callers from growing two subtly different lookup rules.
    """
    lesson = get_lesson(lesson_id)
    if not lesson:
        return None
    linked = lesson.get("linked_support")
    if linked:
        return get_support(linked)
    return next(
        (row for row in get_release()["supports"] if lesson_id in row.get("linked_lessons", [])),
        None,
    )


def get_pinned_release(db, content_release_id: int) -> dict[str, Any]:
    """Read the original private V2 bank bound to a student's release ID.

    The stored checksum and version are authoritative. The current compiler
    may be consulted only for an exact checksum/version match when old data
    predates private snapshots; a different bank never substitutes silently.
    """
    from fastapi import HTTPException
    from db.models import ContentRelease
    from db.learning_models import PrivateContentBankSnapshot

    record = db.query(ContentRelease).filter(ContentRelease.id == content_release_id).one_or_none()
    if record is None:
        raise HTTPException(status_code=409, detail="إصدار محتوى رحلة الطالب غير مسجل")
    frozen = db.query(PrivateContentBankSnapshot).filter(
        PrivateContentBankSnapshot.content_release_id == record.id,
    ).one_or_none()
    if frozen:
        snapshot = frozen.payload_json
        if (not isinstance(snapshot, dict) or frozen.checksum != record.checksum
                or snapshot.get("checksum") != record.checksum
                or snapshot.get("version") != record.version
                or any(not isinstance(snapshot.get(kind), list)
                       for kind in ("lessons", "questions", "supports", "media"))):
            raise HTTPException(status_code=409, detail="بصمة أو بنية محتوى الجلسة لا تطابق النسخة الأصلية")
        return snapshot
    current = get_release()
    if current["checksum"] == record.checksum and current["version"] == record.version:
        return current
    raise HTTPException(status_code=409, detail="النسخة الأصلية غير محفوظة؛ أوقفنا الجلسة لحماية الإجابات")
