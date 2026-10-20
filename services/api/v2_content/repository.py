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
