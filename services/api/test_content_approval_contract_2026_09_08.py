"""Static semantic gates for the canonical 2026-09-08 approval contract."""
from __future__ import annotations

from content_approval_contract_2026_09_08 import (
    CONTEXT_INTROS,
    INTERACTION_OVERRIDES,
    ITEM_MEDIA,
    OPTION_CONTRACTS,
    POSTTEST_STIMULUS_OVERRIDES,
    STEP_MEDIA,
    TIMED_WORD_SELECTIONS,
)
from content_option_lifecycle import visible_key


def _texts(canonical: str, round_number: int = 1) -> list[str]:
    return [text for text, _ in OPTION_CONTRACTS[canonical][round_number - 1]]


def _correct(canonical: str, round_number: int = 1) -> list[str]:
    return [text for text, correct in OPTION_CONTRACTS[canonical][round_number - 1] if correct]


def test_post_q11_is_unified_on_ma():
    assert _texts("POST-Q11") == ["مَ", "مِ", "مُ"]
    assert _correct("POST-Q11") == ["مَ"]
    assert POSTTEST_STIMULUS_OVERRIDES["POST-Q11"] == {"kind": "audio", "audio_target": "مَ"}
    assert STEP_MEDIA["POST-Q11"][1] == [("LET-01", "audio", "prompt", "مَ")]


def test_fourth_choice_is_selective_not_global():
    assert len(_texts("PRE-Q05")) == 4
    assert len(_texts("PRE-Q12")) == 4
    assert len(_texts("L1-CORE-02", 1)) == 4
    assert len(_texts("L2-CORE-05", 1)) == 4
    assert len(_texts("L3-CORE-07", 1)) == 4
    assert len(_texts("POST-Q05")) == 4
    # Natural three-way contracts intentionally remain three.
    assert len(_texts("POST-Q08")) == 3
    assert len(_texts("POST-Q11")) == 3
    assert len(_texts("POST-Q13")) == 3


def test_layan_core_story_has_four_fair_choices_and_intro_audio():
    assert all(len(round_contract) == 4 for round_contract in OPTION_CONTRACTS["L1-CORE-09"])
    assert CONTEXT_INTROS["L1-CORE-09"]["audio_asset_id"] == "INS-01"
    assert ITEM_MEDIA["L1-CORE-09"][0][0] == "INS-01"


def test_nader_reinforcement_keeps_simpler_story_contract():
    assert CONTEXT_INTROS["L1-REIN-11"]["audio_asset_id"] == "INS-02"
    assert ITEM_MEDIA["L1-REIN-11"][0][0] == "INS-02"


def test_generated_sequence_assets_close_old_sandbox_gaps():
    round_one = [asset_id for asset_id, *_ in STEP_MEDIA["L1-REIN-12"][1]]
    round_five = [asset_id for asset_id, *_ in STEP_MEDIA["L1-REIN-12"][5]]
    assert round_one == ["HIMMA-GEN-SEQ-001", "HIMMA-GEN-SEQ-002"]
    assert round_five == ["HIMMA-GEN-SEQ-005", "HIMMA-GEN-SEQ-006"]


def test_pre_q17_requires_a_real_house_vocabulary_asset():
    specs = STEP_MEDIA["PRE-Q17"][1]
    assert [semantic for *_, semantic in specs] == ["الشمس", "القمر", "الشجرة", "بيت"]
    assert specs[-1][0] == "HIMMA-GEN-VOC-001"


def test_l2_rein_07_is_word_only_reading():
    assert INTERACTION_OVERRIDES["L2-REIN-07"] == "read_aloud"


def test_l3_rein_07_is_three_words_per_round_and_timer_is_internal_contract():
    assert TIMED_WORD_SELECTIONS["L3-REIN-07"] == [
        "باب شمس نخلة",
        "مدرسة عصفور حقيبة",
        "يلعب يكتب يذهب",
    ]


def test_no_invisible_duplicate_choice_contracts():
    ordered = {
        "PRE-Q10", "PRE-Q13", "L3-CORE-10", "POST-Q10", "POST-Q13",
    }
    for canonical, rounds in OPTION_CONTRACTS.items():
        if canonical in ordered:
            continue
        for values in rounds:
            keys = [visible_key(text) for text, _ in values]
            assert len(keys) == len(set(keys)), canonical


def test_raw_instruction_fragments_never_enter_known_regression_options():
    for canonical in ("POST-Q08", "POST-Q13"):
        for text in _texts(canonical):
            assert "اختر" not in text
            assert "كوّن" not in text
            assert "الخيارات" not in text
