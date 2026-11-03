"""Frozen text-only contract across all 62 approved V2 reading activities.

Reference data was checked against the original authored question IDs.
These synthetic transcript tests are NOT real acoustic quality validation:
no child audio, Azure credential, live API or Supabase dependency is used.
"""
from __future__ import annotations

import json
from pathlib import Path
import unicodedata

from v2_reading_engine.policy import evaluate_reading


CASES = json.loads((Path(__file__).resolve().parent / "test_fixtures" /
                    "v2_native_reading_62_references.json").read_text(encoding="utf-8"))
KIND_BY_FOCUS = {
    "syllable_reading": "letter",
    "sound_blending": "word",
    "simple_word_reading": "word",
    "long_word_reading": "word",
    "sentence_reading": "sentence",
    "connected_sentence_reading": "sentence",
    "short_text_reading": "text",
}


def _mode(case):
    return "training" if case["role"] == "guided_practice" else "assessment"


def _remove_diacritics(text):
    return "".join(ch for ch in text
                   if not unicodedata.category(ch).startswith("M"))


def test_the_frozen_reference_covers_exactly_62_unique_v2_readings():
    items = CASES["cases"]
    assert len(items) == 62
    assert len({x["id"] for x in items}) == 62
    assert CASES["contentVersion"].startswith("himma-v2-62@")
    assert {x["focus"] for x in items} == set(KIND_BY_FOCUS)
    assert sum(KIND_BY_FOCUS[x["focus"]] == "letter" for x in items) == 10


def test_every_62_text_reference_is_accepted_when_azure_recognizes_it():
    for case in CASES["cases"]:
        kind = KIND_BY_FOCUS[case["focus"]]
        transcript = (case["reference"] if kind == "letter"
                      else _remove_diacritics(case["reference"]))
        result = evaluate_reading(
            kind=kind, mode=_mode(case), question_id=case["id"],
            reference=case["reference"], transcript=transcript,
            audio_valid=True, provider_usable=True,
        )
        assert result.status == "correct", (case["id"], result)
        assert result.fraction == 1, case["id"]


def test_all_62_recognized_mismatches_are_scored_not_re_recorded():
    for case in CASES["cases"]:
        result = evaluate_reading(
            kind=KIND_BY_FOCUS[case["focus"]], mode=_mode(case),
            question_id=case["id"], reference=case["reference"],
            transcript="كلمة_مختلفة_تماما", audio_valid=True,
            provider_usable=True,
        )
        assert result.status == "incorrect", (case["id"], result)
        assert result.fraction is not None, case["id"]
        assert result.passed_for_progress is False, case["id"]
        if _mode(case) == "training":
            assert result.hint, case["id"]
        else:
            assert result.hint is None, case["id"]


def test_all_62_no_recognition_cannot_change_the_academic_grade():
    for case in CASES["cases"]:
        result = evaluate_reading(
            kind=KIND_BY_FOCUS[case["focus"]], mode=_mode(case),
            question_id=case["id"], reference=case["reference"],
            transcript=None, audio_valid=True, provider_usable=False,
        )
        assert result.status == "retry_audio", case["id"]
        assert result.fraction is None and result.passed_for_progress is None
