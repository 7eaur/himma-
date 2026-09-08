"""Listening-media regressions around September image-choice changes.

Several approved activities change image pools while keeping the heard sound.
The canonical compiler must not erase that independent audio target when it
replaces image media. Final runtime receives one explicit semantic prompt audio
plus the approved image choices.
"""
from canonical_release import build_canonical_release


def _by_id():
    release = build_canonical_release()
    return {item["canonical_id"]: item for item in release["items"]}


def _assert_targets(item, expected):
    assert len(item["rounds"]) == len(expected)
    for step, target in zip(item["rounds"], expected, strict=True):
        assert step["stimulus"] == {"kind": "audio", "audio_target": target}
        prompt = [
            asset for asset in step["media"]
            if asset["asset_type"] == "audio" and asset["usage"] == "prompt"
        ]
        assert len(prompt) == 1
        assert prompt[0]["semantic_text"] == target


def test_l1_core_04_keeps_sound_targets_after_four_image_contract():
    items = _by_id()
    item = items["L1-CORE-04"]
    _assert_targets(item, ["م", "ب", "س", "ق", "ن"])
    assert all(
        len([
            asset for asset in step["media"]
            if asset["asset_type"] == "image" and asset["usage"] == "choice"
        ]) == 4
        for step in item["rounds"]
    )


def test_l1_rein_02_keeps_sound_targets_after_two_image_therapy_contract():
    items = _by_id()
    item = items["L1-REIN-02"]
    assert item["interaction_type"] == "listen_choose_image"
    _assert_targets(item, ["م", "ب", "س", "ق", "ن"])
    assert all(
        len([
            asset for asset in step["media"]
            if asset["asset_type"] == "image" and asset["usage"] == "choice"
        ]) == 2
        for step in item["rounds"]
    )


def test_post_q05_keeps_heard_b_after_fourth_image_is_added():
    items = _by_id()
    item = items["POST-Q05"]
    _assert_targets(item, ["ب"])
    step = item["rounds"][0]
    assert len([
        asset for asset in step["media"]
        if asset["asset_type"] == "image" and asset["usage"] == "choice"
    ]) == 4
