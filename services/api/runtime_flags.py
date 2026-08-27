"""Small runtime feature flags used by the recovery/demo branch."""

from __future__ import annotations

import os

_TRUE_VALUES = {"1", "true", "yes", "on", "enabled"}
_FALSE_VALUES = {"0", "false", "no", "off", "disabled"}


def env_flag(name: str, *, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    value = raw.strip().lower()
    if value in _TRUE_VALUES:
        return True
    if value in _FALSE_VALUES:
        return False
    return default


def temporary_audio_skip_enabled() -> bool:
    """Allow neutral skipping of recording tasks while the real audio path is unfinished.

    TEMPORARY — switch HIMMA_TEMP_AUDIO_SKIP=false when the production audio
    pipeline is activated. The recovery branch defaults this flag to enabled so
    the current platform can be exercised end-to-end without a microphone.
    """

    return env_flag("HIMMA_TEMP_AUDIO_SKIP", default=True)
