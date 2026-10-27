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
