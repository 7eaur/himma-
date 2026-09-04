"""Machine-readable regression contract for required fixed/prompt audio gaps."""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "packages" / "content" / "src"
REQUIREMENTS = CONTENT / "audio_asset_requirements_v1.json"
AUDITORY_SOURCE = CONTENT / "l1_auditory_comprehension_v1.json"
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


def test_machine_readable_audio_gap_contract_is_explicit_unique_and_usage_complete():
    payload = json.loads(REQUIREMENTS.read_text(encoding="utf-8"))
    assert payload["version"] == "HIMMA-AUDIO-REQUIREMENTS-1.1"
    assert payload["policy"]["substitution_allowed"] is False
    assert payload["policy"]["placeholder_counts_as_approved"] is False
    assert payload["policy"]["story_text_may_replace_audio_in_student_ui"] is False
    assert payload["policy"]["one_asset_may_have_multiple_usages"] is True

    gaps = payload["known_missing_required_assets"]
    assert [gap["gap_id"] for gap in gaps] == [
        "GAP-AUDIO-01",
        "GAP-AUDIO-02",
        "GAP-AUDIO-03",
        "GAP-AUDIO-04",
    ]
    assert len({gap["gap_id"] for gap in gaps}) == len(gaps)
    assert len({gap["asset_key"] for gap in gaps}) == len(gaps)
    assert all(gap["status"] == "external_content_gap" for gap in gaps)

    by_id = {gap["gap_id"]: gap for gap in gaps}
    assert by_id["GAP-AUDIO-01"]["semantic_text"] == "موز"
    assert by_id["GAP-AUDIO-01"]["usages"] == [
        {"canonical_id": "L1-CORE-06", "round": 1}
    ]
    assert by_id["GAP-AUDIO-02"]["semantic_text"] == "سَا"
    assert by_id["GAP-AUDIO-02"]["usages"] == [
        {"canonical_id": "L2-CORE-06", "round": 4},
        {"canonical_id": "L2-REIN-08", "round": 4},
    ]

    auditory = json.loads(AUDITORY_SOURCE.read_text(encoding="utf-8"))
    auditory_by_id = {item["canonical_id"]: item for item in auditory["items"]}
    story_contracts = {
        "GAP-AUDIO-03": "L1-CORE-09",
        "GAP-AUDIO-04": "L1-REIN-11",
    }
    for gap_id, canonical_id in story_contracts.items():
        gap = by_id[gap_id]
        assert gap["usages"] == [{"canonical_id": canonical_id, "rounds": [1, 2, 3, 4, 5]}]
        assert gap["student_visible_text"] is False
        assert gap["recording_text"] == auditory_by_id[canonical_id]["story_text_internal"]
        assert auditory_by_id[canonical_id]["student_visible_story_text"] is False
        assert auditory_by_id[canonical_id]["audio_asset_id"] is None
        assert auditory_by_id[canonical_id]["audio_status"] == "pending_audio_asset"


def test_known_fixed_word_and_syllable_gaps_are_not_silently_substituted():
    approved = _approved_audio_semantics()
    assert _key("موز") not in approved
    assert _key("سَا") not in approved
    # The existing "موزة" recording is intentionally not accepted as "موز".
    assert _key("موزة") != _key("موز")
