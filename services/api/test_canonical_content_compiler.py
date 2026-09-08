"""Regression coverage for the single canonical Himma content release."""
from __future__ import annotations

import json
from pathlib import Path

from canonical_content_compiler import compile_release
from content_approval_contract_2026_09_08 import VERSION

ROOT = Path(__file__).resolve().parents[2]


def _items():
    release = compile_release()
    return release, {item["canonical_id"]:item for item in release["items"]}


def test_canonical_release_is_complete_deterministic_and_structured():
    first = compile_release()
    second = compile_release()
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


def test_canonical_release_locks_critical_sep8_regressions():
    release, items = _items()

    q11 = items["POST-Q11"]
    step11 = q11["rounds"][0]
    assert q11["criterion"] == "مَ"
    assert [value["text"] for value in step11["options"]] == ["مَ", "مِ", "مُ"]
    assert [value["text"] for value in step11["options"] if value["is_correct"]] == ["مَ"]
    assert step11["stimulus"] == {"kind":"audio","audio_target":"مَ"}
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
        ("HIMMA-GEN-VOC-001", 1),
        ("HIMMA-EDU-VOC-017", 2),
        ("HIMMA-EDU-VOC-018", 3),
        ("HIMMA-EDU-VOC-019", 4),
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


def test_compiled_release_contains_no_unresolved_media_gap():
    release = compile_release()
    unresolved = [
        (item["canonical_id"], step["order_index"], gap)
        for item in release["items"]
        for step in item["rounds"]
        for gap in step.get("media_gaps") or []
    ]
    assert unresolved == []
