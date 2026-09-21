"""Small provider-confusion layer for short Himma pronunciation targets.

Aliases are intentionally weak evidence: a match can prevent an ASR-only false
negative, but it can never mark pronunciation correct by itself.
"""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from typing import Any

from speech_alignment import normalize_arabic

_ALIAS_PATH = Path(__file__).resolve().parents[2] / "packages" / "content" / "src" / "speech_provider_aliases_v1.json"


def _normalize(value: str) -> str:
    return normalize_arabic(value).casefold()


@lru_cache(maxsize=1)
def load_speech_aliases() -> dict[str, dict[str, Any]]:
    payload = json.loads(_ALIAS_PATH.read_text(encoding="utf-8"))
    rows = payload.get("entries")
    if not isinstance(rows, list):
        raise RuntimeError("speech provider alias file must contain an entries list")

    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError("speech provider alias row must be an object")
        target_id = str(row.get("target_id") or "").strip()
        aliases = row.get("aliases")
        if not target_id or not isinstance(aliases, list):
            raise RuntimeError("speech provider alias target_id and aliases are required")
        if target_id in result:
            raise RuntimeError(f"duplicate speech provider alias entry for {target_id}")
        result[target_id] = {
            **row,
            "aliases": [str(value) for value in aliases if str(value).strip()],
        }
    return result


def alias_evidence(target_id: str, transcript: str | None) -> dict[str, Any]:
    entry = load_speech_aliases().get((target_id or "").strip())
    if entry is None or not (transcript or "").strip():
        return {
            "matched": False,
            "effect": None,
            "matched_alias": None,
        }

    observed = _normalize(transcript or "")
    for alias in entry["aliases"]:
        if _normalize(alias) == observed:
            return {
                "matched": True,
                "effect": entry.get("effect") or "do_not_fail_from_asr_only",
                "matched_alias": alias,
            }

    return {
        "matched": False,
        "effect": entry.get("effect") or "do_not_fail_from_asr_only",
        "matched_alias": None,
    }
