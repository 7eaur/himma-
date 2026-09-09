"""Listening-media regressions around September content changes.

Approved image-pool changes must not erase an independent heard sound, while the
Student Experience v2 onset-comparison task must publish both heard words in the
correct order rather than resurrecting its obsolete single prompt sound.
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


def test_l1_core_06_publishes_both_heard_words_in_order():
    item = _by_id()["L1-CORE-06"]
    expected = [
        (("موز", "ماء"), ("WRD-29", "WRD-11")),
        (("باب", "بطة"), ("WRD-03", "WRD-12")),
        (("قلم", "كرة"), ("WRD-04", "WRD-10")),
        (("سمك", "شمس"), ("WRD-05", "WRD-07")),
        (("نور", "نخلة"), ("WRD-15", "WRD-09")),
    ]
    assert len(item["rounds"]) == len(expected)
    for step, (targets, asset_ids) in zip(item["rounds"], expected, strict=True):
        assert step["stimulus"] == {"kind": "audio_sequence", "audio_targets": list(targets)}
        prompt = [
            asset for asset in step["media"]
            if asset["asset_type"] == "audio" and asset["usage"] == "prompt"
        ]
        assert tuple(asset["semantic_text"] for asset in prompt) == targets
        assert tuple(asset["asset_id"] for asset in prompt) == asset_ids
        assert all(not asset["asset_id"].startswith("LET-") for asset in prompt)


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
