"""Project every declared 2026-09-08 approval into the final release.

This is intentionally table-driven from the pure approval contract. It protects
against applying only a visible subset of the approved wording/options/media
changes while leaving another declared item on a historical runtime value.
"""
from __future__ import annotations

from canonical_release import build_canonical_release
from content_approval_contract_2026_09_08 import (
    CONTEXT_INTROS,
    INTERACTION_OVERRIDES,
    ITEM_MEDIA,
    LAYOUT_HINTS,
    OPTION_CONTRACTS,
    READING_TEXTS,
    STEP_MEDIA,
    SUPPRESS_ITEM_MEDIA,
    TIMED_WORD_SELECTIONS,
)
from content_option_lifecycle import visible_key


def _by_id():
    release = build_canonical_release()
    return {item["canonical_id"]: item for item in release["items"]}


def test_every_declared_option_contract_is_the_current_release_option_set():
    items = _by_id()
    for canonical, expected_rounds in OPTION_CONTRACTS.items():
        item = items[canonical]
        assert len(item["rounds"]) == len(expected_rounds), canonical
        for step, expected in zip(item["rounds"], expected_rounds, strict=True):
            actual = [(value["text"], bool(value["is_correct"])) for value in step["options"]]
            assert actual == list(expected), (canonical, step["order_index"])


def test_every_declared_structural_override_reaches_the_final_release():
    items = _by_id()
    for canonical, interaction in INTERACTION_OVERRIDES.items():
        assert items[canonical]["interaction_type"] == interaction

    for canonical, expected_rounds in READING_TEXTS.items():
        item = items[canonical]
        assert [step["expected_reading_text"] for step in item["rounds"]] == list(expected_rounds)
        assert all(step["options"] == [] for step in item["rounds"])

    for canonical, expected_rounds in TIMED_WORD_SELECTIONS.items():
        item = items[canonical]
        assert [step["expected_reading_text"] for step in item["rounds"]] == list(expected_rounds)
        assert all(step["options"] == [] for step in item["rounds"])

    for canonical, intro in CONTEXT_INTROS.items():
        assert items[canonical].get("context_intro") == intro

    for canonical, layout in LAYOUT_HINTS.items():
        assert items[canonical].get("layout_hint") == layout


def test_every_declared_image_relationship_is_semantic_and_exact():
    items = _by_id()
    for canonical, by_round in STEP_MEDIA.items():
        steps = {int(step["order_index"]): step for step in items[canonical]["rounds"]}
        for round_number, specs in by_round.items():
            step = steps[int(round_number)]
            expected_images = [tuple(spec) for spec in specs if spec[1] == "image"]
            actual_images = [
                (
                    asset["asset_id"],
                    asset["asset_type"],
                    asset["usage"],
                    asset["semantic_text"],
                )
                for asset in step["media"]
                if asset["asset_type"] == "image"
            ]
            assert actual_images == expected_images, (canonical, round_number)

            option_order = {
                visible_key(str(option["text"])): index
                for index, option in enumerate(step["options"], 1)
            }
            for asset in step["media"]:
                if asset["asset_type"] != "image" or asset["usage"] != "choice":
                    continue
                expected_order = option_order[visible_key(str(asset["semantic_text"]))]
                assert asset.get("option_order_index") == expected_order, (
                    canonical,
                    round_number,
                    asset["asset_id"],
                )


def test_every_declared_item_media_and_suppression_reaches_the_final_release():
    items = _by_id()
    for canonical, specs in ITEM_MEDIA.items():
        actual = [
            (
                asset["asset_id"],
                asset["asset_type"],
                asset["usage"],
                asset["semantic_text"],
            )
            for asset in items[canonical]["item_assets"]
        ]
        assert actual == [tuple(spec) for spec in specs], canonical

    for canonical in SUPPRESS_ITEM_MEDIA:
        assert items[canonical]["item_assets"] == [], canonical
