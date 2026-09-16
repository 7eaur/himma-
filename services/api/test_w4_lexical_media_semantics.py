"""W4 regression gates for owner-approved lexical media semantics."""
from __future__ import annotations

from copy import deepcopy

import pytest

from canonical_content_compiler import compile_release
from canonical_release import build_canonical_release
from w4_media_semantics import (
    apply_w4_lexical_media_semantics,
    validate_w4_lexical_media_semantics,
)


def _item(release: dict, canonical_id: str) -> dict:
    return next(
        item
        for item in release["items"]
        if str(item.get("canonical_id") or "") == canonical_id
    )


def _round(release: dict, canonical_id: str, round_number: int) -> dict:
    item = _item(release, canonical_id)
    return next(
        step
        for step in item["rounds"]
        if int(step.get("order_index") or 0) == round_number
    )


def _image(step: dict) -> dict:
    images = [
        asset
        for asset in step.get("media") or []
        if asset.get("asset_type") == "image"
    ]
    assert len(images) == 1
    return images[0]


def test_final_release_emits_exact_direct_lexical_stimulus_contract():
    release = build_canonical_release()

    fish = _image(_round(release, "L2-CORE-09", 3))
    light = _image(_round(release, "L2-CORE-09", 5))

    assert fish == {
        "asset_id": "VOC-05",
        "asset_type": "image",
        "usage": "lexical_stimulus",
        "semantic_text": "سَمَك",
    }
    assert light == {
        "asset_id": "VOC-15",
        "asset_type": "image",
        "usage": "lexical_stimulus",
        "semantic_text": "نُور",
    }
    assert validate_w4_lexical_media_semantics(release) == []


def test_source_asset_swap_cannot_be_relabelled_as_approved_lexical_stimulus():
    release = compile_release()
    tampered = deepcopy(release)
    fish = _image(_round(tampered, "L2-CORE-09", 3))
    fish["asset_id"] = "VOC-15"

    with pytest.raises(RuntimeError, match="approved lexical image VOC-05"):
        apply_w4_lexical_media_semantics(tampered)


def test_final_role_swap_back_to_generic_context_is_rejected():
    release = build_canonical_release()
    tampered = deepcopy(release)
    fish = _image(_round(tampered, "L2-CORE-09", 3))
    fish["usage"] = "context"

    failures = validate_w4_lexical_media_semantics(tampered)
    assert any(
        "L2-CORE-09/R03:usage=context:expected=lexical_stimulus" in failure
        for failure in failures
    )


def test_light_identity_is_not_confused_with_tree_asset():
    release = build_canonical_release()
    tampered = deepcopy(release)
    light = _image(_round(tampered, "L2-CORE-09", 5))
    light["asset_id"] = "VOC-08"

    failures = validate_w4_lexical_media_semantics(tampered)
    assert any(
        "L2-CORE-09/R05:asset=VOC-08:expected=VOC-15" in failure
        for failure in failures
    )
