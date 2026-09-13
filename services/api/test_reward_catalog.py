"""Canonical reward catalog/API contract tests for A10/W4."""

import json
from pathlib import Path

from db.adaptation_models import RewardEvent
from reward_catalog import (
    REWARD_CATALOG_VERSION,
    badge_entry_for_level,
    catalog_payload,
    present_reward,
    star_entry,
)


ROOT = Path(__file__).resolve().parents[2]
ASSET_MAP = ROOT / "assets" / "characters" / "developer" / "asset-map.json"


def test_reward_catalog_matches_approved_badge_asset_map():
    payload = json.loads(ASSET_MAP.read_text(encoding="utf-8"))
    approved = {
        row["id"]: row
        for row in payload["assets"]
        if row.get("kind") == "reward"
    }

    expected = {
        "BDG-01": ("star-one", "نجمة واحدة"),
        "BDG-02": ("stars-two", "نجمتان"),
        "BDG-03": ("stars-three", "ثلاث نجوم"),
        "BDG-04": ("letter-explorer", "شارة مستكشف الحروف"),
        "BDG-05": ("word-hero", "شارة بطل الكلمات"),
        "BDG-06": ("comprehension-star", "شارة نجم الفهم"),
    }
    assert set(approved) == set(expected)
    for asset_id, (slug, title) in expected.items():
        assert approved[asset_id]["slug"] == slug
        assert approved[asset_id]["title_ar"] == title


def test_catalog_has_stable_star_and_level_badge_identity():
    assert REWARD_CATALOG_VERSION == "HIMMA_REWARD_CATALOG_1.0.0"
    assert [star_entry(value).asset_id for value in (1, 2, 3)] == ["BDG-01", "BDG-02", "BDG-03"]
    assert [badge_entry_for_level(value).asset_id for value in (1, 2, 3)] == ["BDG-04", "BDG-05", "BDG-06"]
    assert badge_entry_for_level(3).label == "نجم الفهم"

    payload = catalog_payload()
    assert payload["version"] == REWARD_CATALOG_VERSION
    assert len(payload["entries"]) == 6
    l3 = next(row for row in payload["entries"] if row["catalog_key"] == "level:3:core-complete")
    assert l3 == {
        "catalog_key": "level:3:core-complete",
        "reward_type": "badge",
        "stars": None,
        "reward_key": "level:3:core-complete",
        "level_id": 3,
        "label": "نجم الفهم",
        "asset_id": "BDG-06",
        "asset_slug": "comprehension-star",
    }


def test_reward_catalog_endpoint_requires_auth_and_returns_same_version(student_client):
    response = student_client.get("/reward-catalog")
    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == REWARD_CATALOG_VERSION
    assert {row["asset_id"] for row in payload["entries"]} == {
        "BDG-01", "BDG-02", "BDG-03", "BDG-04", "BDG-05", "BDG-06"
    }


def test_historical_l3_label_is_preserved_but_api_uses_canonical_catalog_label():
    historical = RewardEvent(
        id=77,
        student_id=1,
        attempt_id=None,
        reward_type="badge",
        reward_key="level:3:core-complete",
        stars=None,
        label="قارئ متميز",
        details={"event": "level_core_flow_completed", "level_id": 3},
    )
    payload = present_reward(historical)

    assert payload["key"] == "level:3:core-complete"
    assert payload["label"] == "نجم الفهم"
    assert payload["recorded_label"] == "قارئ متميز"
    assert payload["catalog_version"] == REWARD_CATALOG_VERSION
    assert payload["asset_id"] == "BDG-06"
    assert payload["asset_slug"] == "comprehension-star"


def test_unknown_historical_reward_remains_readable_without_fake_asset_identity():
    historical = RewardEvent(
        id=78,
        student_id=1,
        attempt_id=None,
        reward_type="badge",
        reward_key="legacy:badge:unknown",
        stars=None,
        label="شارة تاريخية",
        details={"legacy": True},
    )
    payload = present_reward(historical)

    assert payload["label"] == "شارة تاريخية"
    assert payload["recorded_label"] == "شارة تاريخية"
    assert payload["catalog_version"] == REWARD_CATALOG_VERSION
    assert payload["asset_id"] is None
    assert payload["asset_slug"] is None
