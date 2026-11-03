"""Owner-approved media replacements without rewriting frozen academic banks.

Only the exact temporary video contract may be superseded. Missing or altered
approved replacements fail closed; they never fall back to the retired shared clip.
"""

import json
from functools import lru_cache
from pathlib import Path

from .compiler import REPO_ROOT


MANIFEST = REPO_ROOT / "assets/video/lessons/manifest.json"
TEMPORARY_SOURCE = "assets/video/HIMMA_V2_DEMO/gemini_generated_video_72256b30.mp4"
TEMPORARY_SHA256 = "57e6c7a1d6316a6d1306493dfe81f13dba56c94392f0c63d48bc1146c5252590"


@lru_cache(maxsize=1)
def approved_lesson_videos() -> dict:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if payload.get("schema") != "himma-approved-lesson-videos/1" or not isinstance(payload.get("videos"), dict):
        raise ValueError("Invalid approved lesson-video manifest")
    return payload["videos"]


def lesson_video_replacement(asset: dict) -> dict | None:
    """Return an explicit media-only override, never change the release itself."""
    if ((asset.get("kind") or asset.get("type")) != "video"
            or asset.get("status") != "approved_temporary"
            or asset.get("shared_temporary_video") is not True
            or asset.get("source_path") != TEMPORARY_SOURCE
            or asset.get("source_sha256") != TEMPORARY_SHA256):
        return None
    entry = approved_lesson_videos().get(asset.get("id"))
    if entry is None:
        return None
    lesson_id = str(asset["id"]).removeprefix("VID-")
    expected = f"assets/video/lessons/HIMMA_{lesson_id}_480p.mp4"
    if (entry.get("lesson_id") != lesson_id or entry.get("source_path") != expected
            or entry.get("status") != "approved"
            or len(str(entry.get("source_sha256", ""))) != 64):
        raise ValueError("Invalid approved lesson-video binding")
    return dict(asset, status="approved", source_path=expected,
                source_sha256=entry["source_sha256"], shared_temporary_video=False)
