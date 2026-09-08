"""Regression gates for the canonical 30-question posttest presentation.

The old Sep-01 DB overlay is no longer executable authority. Its approved display
fields are now a pure compiler input and the newer Sep-08 changes must win before
publication. These tests protect the student-visible stimuli, reading targets and
assessment projection from falling back to raw legacy source text.
"""
from __future__ import annotations

import seed_all
from canonical_release import build_canonical_release
from content_runtime import canonical_id
from db.database import SessionLocal
from db.models import ContentItem
from posttest_presentation_2026_09_01 import POSTTEST_PRESENTATION


def _items():
    release = build_canonical_release()
    return {item["canonical_id"]: item for item in release["items"]}


def test_posttest_presentation_source_covers_all_30_questions_exactly():
    assert set(POSTTEST_PRESENTATION) == {f"POST-Q{number:02d}" for number in range(1, 31)}


def test_posttest_final_release_has_structured_nonlegacy_stimuli():
    items = _items()
    expected = {
        "POST-Q01": {"kind": "text", "text": "ت"},
        "POST-Q02": {"kind": "text", "text": "خ"},
        "POST-Q03": {"kind": "text", "text": "س"},
        "POST-Q04": {"kind": "audio", "audio_target": "ق"},
        "POST-Q05": {"kind": "audio", "audio_target": "ب"},
        "POST-Q06": {"kind": "audio", "audio_target": "نَخْلَة"},
        "POST-Q07": {"kind": "audio", "audio_target": "قَمَر"},
        "POST-Q08": {"kind": "none"},
        "POST-Q09": {"kind": "none"},
        "POST-Q10": {"kind": "none"},
        # Sep-08 correction must override the historical Sep-01 مِ.
        "POST-Q11": {"kind": "audio", "audio_target": "مَ"},
        "POST-Q12": {"kind": "audio", "audio_target": "نُو"},
        "POST-Q13": {"kind": "text", "text": "مَكْتَب"},
        "POST-Q14": {"kind": "image", "text": "نَخْلَة"},
        "POST-Q15": {"kind": "text", "text": "فِيل"},
        "POST-Q16": {"kind": "text", "text": "بَـ _ ـر"},
        "POST-Q17": {"kind": "text", "text": "قَمَر"},
        "POST-Q18": {"kind": "audio", "audio_target": "سُوق"},
        "POST-Q25": {"kind": "reference"},
        "POST-Q26": {"kind": "reference"},
        "POST-Q27": {"kind": "reference"},
        "POST-Q28": {"kind": "reference"},
        "POST-Q29": {"kind": "reference"},
        "POST-Q30": {"kind": "text", "text": "أَصْدَافًا مُلَوَّنَةً"},
    }
    for canonical, stimulus in expected.items():
        assert items[canonical]["rounds"][0]["stimulus"] == stimulus, canonical


def test_posttest_reading_questions_are_recording_only_with_exact_text():
    items = _items()
    expected = {
        "POST-Q19": "رَسَمَ",
        "POST-Q20": "نَجْم",
        "POST-Q21": "نُور",
        "POST-Q22": "سُلَّم",
        "POST-Q23": "تَلْعَبُ مَرْيَمُ بِالْكُرَةِ.",
        "POST-Q24": "فِي صَبَاحٍ مُشْمِسٍ، ذَهَبَ مَاجِدٌ مَعَ وَالِدِهِ إِلَى الشَّاطِئِ. أَخَذَ دَلْوًا صَغِيرًا، وَحَمَلَ وَالِدُهُ مَاءً وَمِظَلَّةً. بَنَى مَاجِدٌ بَيْتًا مِنَ الرَّمْلِ، ثُمَّ جَمَعَ أَصْدَافًا مُلَوَّنَةً. قَبْلَ الْعَوْدَةِ، نَظَّفَا مَكَانَهُمَا.",
    }
    for canonical, text in expected.items():
        item = items[canonical]
        step = item["rounds"][0]
        assert item["interaction_type"] in {"read_aloud", "timed_read_aloud"}
        assert step["expected_reading_text"] == text
        assert step["options"] == []
        assert step["stimulus"] == {"kind": "reading", "text": text}


def test_posttest_exact_presentation_fields_reach_the_db_projection():
    result = seed_all.run_seed_all()
    assert result["posttest_experience_items"] == 30

    db = SessionLocal()
    try:
        by_id = {
            canonical_id(item): item
            for item in db.query(ContentItem).filter(ContentItem.kind == "posttest_question").all()
        }
        for canonical, source in POSTTEST_PRESENTATION.items():
            experience = (by_id[canonical].template_data or {})["posttest_experience"]
            step = by_id[canonical].steps[0]
            assert experience["skill"] == source["skill"], canonical
            assert experience["instruction_text"] == source["instruction_text"], canonical
            assert experience["encouragement"] == source["encouragement"], canonical
            expected_stimulus = source["stimulus"]
            if canonical == "POST-Q11":
                expected_stimulus = {"kind": "audio", "audio_target": "مَ"}
            assert experience["stimulus"] == expected_stimulus, canonical
            if "expected_reading_text" in source:
                assert step.expected_reading_text == source["expected_reading_text"], canonical

        # Story-comprehension rounds are intentionally question-only: no story image.
        for number in range(25, 31):
            assert by_id[f"POST-Q{number:02d}"].assets == []
    finally:
        db.close()
