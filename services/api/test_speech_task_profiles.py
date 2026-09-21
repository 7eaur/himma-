import json
from pathlib import Path

import pytest

from speech_task_profiles import load_speech_task_profiles, profile_for, require_profile


ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "packages" / "content" / "src" / "catalog.json"


def _recording_items():
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return [
        item
        for item in catalog["items"]
        if item.get("interaction_type") in {"read_aloud", "timed_read_aloud"}
    ]


def test_every_current_recording_item_has_an_explicit_speech_profile():
    items = _recording_items()
    profiles = load_speech_task_profiles()

    assert len(items) == 26
    assert sum(len(item.get("rounds") or []) for item in items) == 71
    assert {item["canonical_id"] for item in items} == set(profiles)


def test_profiles_use_only_the_three_simplified_modes():
    profiles = load_speech_task_profiles()
    assert {profile.mode for profile in profiles.values()} == {
        "targeted_pronunciation",
        "lexical",
        "fluency",
    }


@pytest.mark.parametrize(
    ("canonical_id", "mode", "focus"),
    [
        ("L1-REIN-05", "targeted_pronunciation", "short_vowel"),
        ("L2-CORE-10", "lexical", None),
        ("L3-CORE-06", "fluency", "timed_passage"),
    ],
)
def test_representative_profiles(canonical_id, mode, focus):
    profile = require_profile(canonical_id)
    assert profile.mode == mode
    assert profile.focus == focus


def test_unknown_content_fails_closed_instead_of_guessing_from_diacritics():
    assert profile_for("NEW-READING-CONTENT") is None
    with pytest.raises(LookupError):
        require_profile("NEW-READING-CONTENT")
