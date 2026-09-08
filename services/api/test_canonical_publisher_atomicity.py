"""Transactional bootstrap regression gates for the canonical publisher.

A fresh database must never be left with 105/125 partially committed structural
rows when the final current publication fails. All content structure, options,
media, scoring compatibility and release activation now belong to one publisher
transaction.
"""
from __future__ import annotations

import pytest

import canonical_content_publisher as publisher
from canonical_release import build_canonical_release
from db.database import SessionLocal
from db.models import (
    ContentAssetLink,
    ContentItem,
    ContentOption,
    ContentRelease,
    ContentStep,
    ScoringPolicy,
    ScoringRule,
    Skill,
)


def _counts() -> dict[str, int]:
    db = SessionLocal()
    try:
        return {
            "skills": db.query(Skill).count(),
            "items": db.query(ContentItem).count(),
            "steps": db.query(ContentStep).count(),
            "options": db.query(ContentOption).count(),
            "assets": db.query(ContentAssetLink).count(),
            "policies": db.query(ScoringPolicy).count(),
            "rules": db.query(ScoringRule).count(),
            "releases": db.query(ContentRelease).count(),
        }
    finally:
        db.close()


def test_fresh_publication_rolls_back_all_structure_when_current_projection_fails(monkeypatch):
    release = build_canonical_release()
    assert _counts() == {
        "skills": 0,
        "items": 0,
        "steps": 0,
        "options": 0,
        "assets": 0,
        "policies": 0,
        "rules": 0,
        "releases": 0,
    }

    def fail_publish(*_args, **_kwargs):
        raise RuntimeError("forced publication failure after structural bootstrap")

    monkeypatch.setattr(publisher, "_publish_item", fail_publish)
    with pytest.raises(RuntimeError, match="forced publication failure"):
        publisher.publish_release(release)

    # No legacy importer committed an intermediate 105/125-item state.
    assert _counts() == {
        "skills": 0,
        "items": 0,
        "steps": 0,
        "options": 0,
        "assets": 0,
        "policies": 0,
        "rules": 0,
        "releases": 0,
    }


def test_fresh_canonical_publish_creates_complete_structure_and_second_publish_is_noop():
    release = build_canonical_release()
    first = publisher.publish_release(release)
    first_counts = _counts()
    second = publisher.publish_release(release)
    second_counts = _counts()

    assert first["items"] == 125
    assert first["baseline_rows_created"] == 105
    assert first["v1_rows_created"] == 18
    assert first["v2_rows_created"] == 2
    assert first["scoring_rules_created"] == 60

    assert second["baseline_rows_created"] == 0
    assert second["v1_rows_created"] == 0
    assert second["v2_rows_created"] == 0
    assert second["scoring_rules_created"] == 0
    assert second["option_rows_created"] == 0
    assert second["option_rows_reactivated"] == 0
    assert second["option_rows_retired"] == 0
    assert second["asset_rows_created"] == 0
    assert second["asset_rows_retired"] == 0
    assert first["release_sha256"] == second["release_sha256"]
    assert first["projection_sha256"] == second["projection_sha256"]
    assert first_counts == second_counts

    assert first_counts["skills"] == 44
    assert first_counts["items"] == 125
    assert first_counts["policies"] == 1
    assert first_counts["rules"] == 60
    assert first_counts["releases"] == 1
