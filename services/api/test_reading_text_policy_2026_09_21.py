"""Regression gates for the 2026-09-21 reading-text presentation policy."""
from __future__ import annotations

import json
import re
from pathlib import Path

from canonical_release import build_canonical_release
from reading_text_policy_2026_09_21 import normalize_reading_text

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "packages" / "content" / "training" / "himma_reading_training_corpus_v2026_09_21.jsonl"
READ = {"read_aloud", "timed_read_aloud"}
NON_SHADDA_ARABIC_MARKS = re.compile(r"[\u0610-\u061a\u064b-\u0650\u0652-\u065f\u0670\u06d6-\u06ed]")


def test_single_letters_syllables_and_words_keep_full_diacritics():
    values = ["م", "مَ", "قِطَّة", "سُلَّم", "مُعَلِّم"]
    assert [normalize_reading_text(value) for value in values] == values


def test_multiword_text_drops_optional_marks_but_keeps_shadda():
    source = "فِي صَبَاحٍ، ثُمَّ حَمَلَتْ سَلَّةَ الطَّعَامِ."
    assert normalize_reading_text(source) == "في صباح، ثمّ حملت سلّة الطّعام."


def test_final_release_has_no_optional_arabic_marks_in_multiword_reading_text():
    release = build_canonical_release()
    for item in release["items"]:
        for step in item.get("rounds") or []:
            text = step.get("expected_reading_text")
            if text and re.search(r"\s", text.strip()):
                assert not NON_SHADDA_ARABIC_MARKS.search(text), (item["canonical_id"], text)
        intro = item.get("context_intro") or {}
        if intro.get("kind") == "reading_context":
            assert not NON_SHADDA_ARABIC_MARKS.search(str(intro.get("text") or "")), item["canonical_id"]


def test_training_corpus_exactly_matches_final_release_reading_targets():
    release = build_canonical_release()
    expected = {}
    for item in release["items"]:
        canonical = item["canonical_id"]
        if item.get("interaction_type") in READ:
            for step in item.get("rounds") or []:
                expected[f"{canonical}-R{int(step['order_index']):02d}"] = step["expected_reading_text"]
        intro = item.get("context_intro") or {}
        if intro.get("kind") == "reading_context":
            expected[f"{canonical}-CONTEXT"] = intro["text"]

    records = [json.loads(line) for line in CORPUS.read_text(encoding="utf-8").splitlines() if line.strip()]
    actual = {record["id"]: record["text"] for record in records}

    assert len(records) == 92
    assert len(actual) == 92
    assert actual == expected
