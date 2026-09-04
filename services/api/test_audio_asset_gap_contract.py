"""Machine-readable regression contract for required fixed/prompt audio gaps."""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REQUIREMENTS = ROOT / "packages" / "content" / "src" / "audio_asset_requirements_v1.json"
AUDIO_MANIFEST = ROOT / "assets" / "audio" / "HIMMA_AUDIO_V1" / "manifest.csv"


def _key(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = re.sub(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]", "", value)
    value = value.replace("ـ", "")
    value = re.sub(r"[^\w\u0600-\u06ff]+", "", value, flags=re.UNICODE)
    return value.casefold()


def _approved_audio_semantics() -> set[str]:
    values: set[str] = set()
    with AUDIO_MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("status") != "approved":
                continue
            for field in ("text_ar", "spoken_input"):
                normalized = _key(str(row.get(field) or ""))
                if normalized:
                    values.add(normalized)
    return values


def test_machine_readable_audio_gap_contract_is_explicit_and_unique():
    payload = json.loads(REQUIREMENTS.read_text(encoding="utf-8"))
    assert payload["version"] == "HIMMA-AUDIO-REQUIREMENTS-1.0"
    assert payload["policy"]["substitution_allowed"] is False
    assert payload["policy"]["placeholder_counts_as_approved"] is False
    assert payload["policy"]["story_text_may_replace_audio_in_student_ui"] is False

    gaps = payload["known_missing_required_assets"]
    assert [gap["gap_id"] for gap in gaps] == [
        "GAP-AUDIO-01",
        "GAP-AUDIO-02",
        "GAP-AUDIO-03",
        "GAP-AUDIO-04",
    ]
    assert len({gap["gap_id"] for gap in gaps}) == len(gaps)
    assert all(gap["status"] == "external_content_gap" for gap in gaps)

    by_id = {gap["gap_id"]: gap for gap in gaps}
    assert by_id["GAP-AUDIO-01"]["canonical_id"] == "L1-CORE-06"
    assert by_id["GAP-AUDIO-01"]["semantic_text"] == "موز"
    assert by_id["GAP-AUDIO-02"]["canonical_id"] == "L2-CORE-06"
    assert by_id["GAP-AUDIO-02"]["semantic_text"] == "سَا"

    for gap_id in ("GAP-AUDIO-03", "GAP-AUDIO-04"):
        gap = by_id[gap_id]
        assert gap["rounds"] == [1, 2, 3, 4, 5]
        assert gap["student_visible_text"] is False
        assert gap["recording_text"].strip()


def test_known_fixed_word_and_syllable_gaps_are_not_silently_substituted():
    approved = _approved_audio_semantics()
    assert _key("موز") not in approved
    assert _key("سَا") not in approved
