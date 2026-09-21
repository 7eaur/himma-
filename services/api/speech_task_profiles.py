"""Explicit speech-task routing for Himma's simplified speech model.

Routing is content-driven and intentionally independent from diacritic density.
The canonical IDs in packages/content/src/speech_task_profiles_v1.json decide
whether a recording is lexical, targeted pronunciation, or fluency.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
from typing import Literal

SpeechMode = Literal["targeted_pronunciation", "lexical", "fluency"]
_ALLOWED_MODES: set[str] = {"targeted_pronunciation", "lexical", "fluency"}
_PROFILE_PATH = Path(__file__).resolve().parents[2] / "packages" / "content" / "src" / "speech_task_profiles_v1.json"


@dataclass(frozen=True)
class SpeechTaskProfile:
    canonical_id: str
    mode: SpeechMode
    focus: str | None


@lru_cache(maxsize=1)
def load_speech_task_profiles() -> dict[str, SpeechTaskProfile]:
    payload = json.loads(_PROFILE_PATH.read_text(encoding="utf-8"))
    rows = payload.get("profiles")
    if not isinstance(rows, list):
        raise RuntimeError("speech task profile file must contain a profiles list")

    profiles: dict[str, SpeechTaskProfile] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError("speech task profile row must be an object")
        canonical_id = str(row.get("canonical_id") or "").strip()
        mode = str(row.get("mode") or "").strip()
        focus_value = row.get("focus")
        focus = str(focus_value).strip() if focus_value is not None else None

        if not canonical_id:
            raise RuntimeError("speech task profile canonical_id is required")
        if mode not in _ALLOWED_MODES:
            raise RuntimeError(f"unsupported speech mode {mode!r} for {canonical_id}")
        if canonical_id in profiles:
            raise RuntimeError(f"duplicate speech task profile for {canonical_id}")

        profiles[canonical_id] = SpeechTaskProfile(
            canonical_id=canonical_id,
            mode=mode,  # type: ignore[arg-type]
            focus=focus or None,
        )

    return profiles


def profile_for(canonical_id: str) -> SpeechTaskProfile | None:
    return load_speech_task_profiles().get((canonical_id or "").strip())


def require_profile(canonical_id: str) -> SpeechTaskProfile:
    profile = profile_for(canonical_id)
    if profile is None:
        raise LookupError(f"speech task {canonical_id!r} has no explicit profile")
    return profile
