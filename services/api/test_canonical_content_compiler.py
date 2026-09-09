"""Regression coverage for the single final Himma canonical release."""
from __future__ import annotations

import json
from pathlib import Path

from canonical_media_guard import validate_media_contract
from canonical_release import build_canonical_release
from content_approval_contract_2026_09_08 import (
    LEARNING_QUESTIONS,
    LEARNING_ROUND_QUESTIONS,
    POSTTEST_QUESTIONS,
    PRETEST_QUESTIONS,
    VERSION,
)
from listening_sequence_contract_2026_09_03 import LISTENING_AUDIO_SEQUENCES

ROOT = Path(__file__).resolve().parents[2]
STRUCTURED_STORY_QUESTION_SOURCES = {"L1-CORE-09", "L1-REIN-11"}


def _items():
    release = build_canonical_release()
    return release, {item["canonical_id"]: item for item in release["items"]}


def test_canonical_release_is_complete_deterministic_and_structured():
    first = build_canonical_release()
    second = build_canonical_release()
    assert first["release_version"] == VERSION
    assert first["sha256"] == second["sha256"]
    assert len(first["items"]) == 125
    assert len({item["canonical_id"] for item in first["items"]}) == 125
    assert sum(item["kind"] == "pretest_question" for item in first["items"]) == 30
    assert sum(item["kind"] == "posttest_question" for item in first["items"]) == 30
    assert sum(item["kind"] == "core_activity" for item in first["items"]) == 30
    assert sum(item["kind"] == "reinforcement_activity" for item in first["items"]) == 35

    for item in first["items"]:
        assert item["release_version"] == VERSION
        assert item["rounds"]
        for step in item["rounds"]:
            assert step["question_text"].strip()
            assert step["instruction_text"].strip()
            assert step["hint"].strip()
            assert step["encouragement"].strip()
            assert "source_text" not in step


def test_every_student_question_is_accounted_for_by_an_approved_structured_source():
    release = build_canonical_release()
    pretest = {
        item["canonical_id"] for item in release["items"]
        if item["kind"] == "pretest_question"
    }
    posttest = {
        item["canonical_id"] for item in release["items"]
        if item["kind"] == "posttest_question"
    }
    learning = {
        item["canonical_id"] for item in release["items"]
        if item["kind"] in {"core_activity", "reinforcement_activity"}
    }

    assert pretest == set(PRETEST_QUESTIONS)
    assert posttest == set(POSTTEST_QUESTIONS)
    assert learning == (
        set(LEARNING_QUESTIONS)
        | set(LEARNING_ROUND_QUESTIONS)
        | STRUCTURED_STORY_QUESTION_SOURCES
    )
    assert len(learning) == 65

    by_id = {item["canonical_id"]: item for item in release["items"]}
    for canonical, questions in LEARNING_ROUND_QUESTIONS.items():
        assert len(by_id[canonical]["rounds"]) == len(questions)
        assert [step["question_text"] for step in by_id[canonical]["rounds"]] == questions

    for canonical in STRUCTURED_STORY_QUESTION_SOURCES:
        assert all(step["question_text"].strip() for step in by_id[canonical]["rounds"])


def test_canonical_release_locks_critical_sep8_regressions():
    _release, items = _items()

    q11 = items["POST-Q11"]
    step11 = q11["rounds"][0]
    assert q11["criterion"] == "مَ"
    assert [value["text"] for value in step11["options"]] == ["مَ", "مِ", "مُ"]
    assert [value["text"] for value in step11["options"] if value["is_correct"]] == ["مَ"]
    assert step11["stimulus"] == {"kind": "audio", "audio_target": "مَ"}
    assert [(value["asset_id"], value["usage"]) for value in step11["media"] if value["asset_type"] == "audio"] == [("LET-01", "prompt")]

    assert [value["text"] for value in items["POST-Q08"]["rounds"][0]["options"]] == [
        "ل", "كِتَاب", "قَرَأَ خَالِدٌ الْكِتَابَ."
    ]
    assert [value["text"] for value in items["POST-Q13"]["rounds"][0]["options"]] == ["مَكْ", "تَب", "نُور"]

    l2 = items["L2-REIN-07"]
    assert l2["interaction_type"] == "read_aloud"
    assert [value["expected_reading_text"] for value in l2["rounds"]] == ["كَتَبَ", "لَعِبَ", "رَسَمَ", "فَتَحَ", "جَلَسَ"]
    assert all(value["options"] == [] for value in l2["rounds"])

    assert [value["expected_reading_text"] for value in items["L3-REIN-07"]["rounds"]] == [
        "باب شمس نخلة", "مدرسة عصفور حقيبة", "يلعب يكتب يذهب"
    ]


def test_every_listening_round_has_an_explicit_semantic_prompt_contract():
    _release, items = _items()
    seen = 0
    for item in items.values():
        if not str(item["interaction_type"]).startswith("listen_"):
            continue
        canonical = item["canonical_id"]
        sequences = LISTENING_AUDIO_SEQUENCES.get(canonical)
        for step in item["rounds"]:
            seen += 1
            prompt_audio = [
                value for value in step["media"]
                if value["asset_type"] == "audio" and value["usage"] == "prompt"
            ]
            if sequences is not None:
                targets = sequences[int(step["order_index"]) - 1]
                assert len(prompt_audio) == len(targets)
                assert [value["semantic_text"] for value in prompt_audio] == list(targets)
                assert step["stimulus"] == {
                    "kind": "audio_sequence",
                    "audio_targets": list(targets),
                }
            else:
                assert len(prompt_audio) == 1, (canonical, step["order_index"])
                assert step["stimulus"] == {
                    "kind": "audio",
                    "audio_target": prompt_audio[0]["semantic_text"],
                }
    assert seen > 0

    # The final audio package changed LET-01 to مَ. A vocalized مِ target must
    # therefore resolve to its exact syllable asset instead of reusing LET-01.
    l2_short_vowel = items["L2-CORE-01"]["rounds"][1]
    assert l2_short_vowel["stimulus"] == {"kind": "audio", "audio_target": "مِ"}
    assert [
        value["asset_id"] for value in l2_short_vowel["media"]
        if value["asset_type"] == "audio" and value["usage"] == "prompt"
    ] == ["SYL-05"]

    # Bare letter م remains a letter-sound target and intentionally resolves to
    # stable LET-01, whose approved current recording is مَ.
    pre_q05 = items["PRE-Q05"]["rounds"][0]
    assert pre_q05["stimulus"] == {"kind": "audio", "audio_target": "م"}
    assert [value["asset_id"] for value in pre_q05["media"] if value["asset_type"] == "audio"] == ["LET-01"]


def test_story_and_image_contracts_are_explicit_not_positional():
    _, items = _items()
    for canonical, asset_id in (("L1-CORE-09", "INS-01"), ("L1-REIN-11", "INS-02")):
        item = items[canonical]
        assert item["canonical_skill_code"] == "auditory_literal_comprehension"
        assert item["context_intro"]["kind"] == "audio_story"
        assert item["context_intro"]["audio_asset_id"] == asset_id
        assert [value["asset_id"] for value in item["item_assets"]] == [asset_id]
        assert all(not [asset for asset in step["media"] if asset["asset_type"] == "audio"] for step in item["rounds"])

    for item in items.values():
        for step in item["rounds"]:
            choice_images = [asset for asset in step["media"] if asset["asset_type"] == "image" and asset["usage"] == "choice"]
            orders = [asset.get("option_order_index") for asset in choice_images]
            assert all(order is not None for order in orders)
            assert len(orders) == len(set(orders))

    for prefix in ("PRE-Q", "POST-Q"):
        for number in range(25, 31):
            assert items[f"{prefix}{number:02d}"]["item_assets"] == []


def test_pre_q17_generated_house_closes_the_last_proven_vocabulary_media_gap():
    _, items = _items()
    step = items["PRE-Q17"]["rounds"][0]

    assert step["media_gaps"] == []
    choice_images = [
        asset for asset in step["media"]
        if asset["asset_type"] == "image" and asset["usage"] == "choice"
    ]
    assert [(asset["asset_id"], asset["option_order_index"]) for asset in choice_images] == [
        ("VOC-06", 1),
        ("VOC-07", 2),
        ("VOC-08", 3),
        ("HIMMA-GEN-VOC-001", 4),
    ]

    generated_map = ROOT / "assets" / "education" / "developer" / "generated-vocabulary-map.json"
    payload = json.loads(generated_map.read_text(encoding="utf-8"))
    record = next(asset for asset in payload["assets"] if asset["id"] == "HIMMA-GEN-VOC-001")
    assert record["semantic_key"] == "بيت"
    assert record["qa"]["no_embedded_text"] is True
    assert record["qa"]["single_subject"] is True
    relative = record["files"]["webp_small"]
    image_path = ROOT / "assets" / "education" / relative
    assert image_path.is_file()
    assert image_path.stat().st_size > 0


def test_compiled_release_contains_no_unresolved_media_gap_or_missing_binary():
    release = build_canonical_release()
    unresolved = [
        (item["canonical_id"], step["order_index"], gap)
        for item in release["items"]
        for step in item["rounds"]
        for gap in step.get("media_gaps") or []
    ]
    assert unresolved == []
    assert all(values == [] for values in validate_media_contract(release).values())
