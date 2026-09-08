"""Regression gates for semantic media identity in the canonical release."""
from __future__ import annotations

from copy import deepcopy

from canonical_media_guard import resolve_audio_asset, validate_media_contract
from canonical_release import build_canonical_release


def _item(release: dict, canonical_id: str) -> dict:
    return next(
        item
        for item in release["items"]
        if str(item.get("canonical_id") or "") == canonical_id
    )


def test_final_canonical_release_has_zero_media_contract_failures():
    release = build_canonical_release()
    result = validate_media_contract(release)
    assert all(not values for values in result.values()), result


def test_choice_image_asset_identity_cannot_be_swapped_by_position():
    release = build_canonical_release()
    tampered = deepcopy(release)
    step = _item(tampered, "PRE-Q05")["rounds"][0]

    banana = next(
        asset
        for asset in step["media"]
        if asset.get("asset_type") == "image"
        and asset.get("usage") == "choice"
        and asset.get("semantic_text") == "موزة"
    )
    # Keep the semantic option/index unchanged but substitute the book asset.
    # A positional-only implementation would accept this; the semantic guard must not.
    banana["asset_id"] = "VOC-02"

    result = validate_media_contract(tampered)
    assert result["image_semantic_mismatches"]
    assert any("PRE-Q05/R01:VOC-02" in value for value in result["image_semantic_mismatches"])


def test_generated_house_is_the_semantic_house_choice_not_a_scene_substitute():
    release = build_canonical_release()
    step = _item(release, "PRE-Q17")["rounds"][0]
    house = next(
        asset
        for asset in step["media"]
        if asset.get("asset_type") == "image"
        and asset.get("usage") == "choice"
        and asset.get("semantic_text") == "بيت"
    )
    assert house["asset_id"] == "HIMMA-GEN-VOC-001"
    assert not validate_media_contract(release)["image_semantic_mismatches"]


def test_vocalized_letter_audio_does_not_collapse_to_another_vowel():
    assert resolve_audio_asset("مَ") == "LET-01"
    try:
        resolve_audio_asset("مِ")
    except RuntimeError as exc:
        assert "exactly one approved asset" in str(exc)
    else:
        raise AssertionError("مِ must not silently resolve to the approved مَ letter-sound asset")
