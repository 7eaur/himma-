"""Full approved runtime content seed entrypoint contract."""

import seed_all
from db.database import SessionLocal
from db.models import ContentAssetLink, ContentItem, ContentOption, ContentRelease, ContentStep


def _runtime_identity_snapshot():
    db = SessionLocal()
    try:
        items = tuple(sorted(
            (
                int(item.id),
                str(item.stable_key),
                str(item.checksum),
                str((item.template_data or {}).get("canonical_release_sha256") or ""),
                str((item.template_data or {}).get("canonical_projection_sha256") or ""),
            )
            for item in db.query(ContentItem).all()
        ))
        steps = tuple(sorted(
            (int(step.id), int(step.item_id), int(step.order_index))
            for step in db.query(ContentStep).all()
        ))
        active_options = tuple(sorted(
            (
                int(option.id), int(option.step_id), int(option.order_index),
                str(option.text), bool(option.is_correct),
            )
            for option in db.query(ContentOption).filter(ContentOption.is_active.is_(True)).all()
        ))
        all_option_count = db.query(ContentOption).count()
        inactive_option_count = db.query(ContentOption).filter(ContentOption.is_active.is_(False)).count()
        media = tuple(sorted(
            (
                int(link.item_id) if link.item_id is not None else None,
                int(link.step_id) if link.step_id is not None else None,
                str(link.manifest_asset_id), str(link.asset_type), str(link.usage_context or ""),
            )
            for link in db.query(ContentAssetLink).all()
        ))
        releases = tuple(sorted(
            (str(row.version), bool(row.is_active))
            for row in db.query(ContentRelease).all()
        ))
        return {
            "items": items,
            "steps": steps,
            "active_options": active_options,
            "all_option_count": all_option_count,
            "inactive_option_count": inactive_option_count,
            "media": media,
            "releases": releases,
        }
    finally:
        db.close()


def test_full_seed_creates_125_items_and_is_repeatable():
    first = seed_all.run_seed_all()
    first_snapshot = _runtime_identity_snapshot()
    second = seed_all.run_seed_all()
    second_snapshot = _runtime_identity_snapshot()

    assert first["baseline_items"] == 105
    assert first["reinforcement_items"] == 35
    assert first["total_items"] == 125
    assert first["v1_additions_created"] == 18
    assert first["v2_additions_created"] == 2
    assert first["additions_created"] == 20

    assert second["baseline_items"] == 105
    assert second["reinforcement_items"] == 35
    assert second["total_items"] == 125
    assert second["v1_additions_created"] == 0
    assert second["v2_additions_created"] == 0
    assert second["additions_created"] == 0

    assert first["canonical_release_sha256"] == second["canonical_release_sha256"]
    assert first["canonical_release_items"] == second["canonical_release_items"] == 125
    assert first["publication"]["projection_sha256"] == second["publication"]["projection_sha256"]
    assert len(second["publication"]["projection_sha256"]) == 64
    assert second["publication"]["option_rows_created"] == 0
    assert second["publication"]["option_rows_reactivated"] == 0
    assert second["publication"]["option_rows_retired"] == 0

    # Item IDs, step IDs and active option IDs are durable. Media link row IDs are
    # intentionally not part of the snapshot because current presentation links
    # may be replaced transactionally, but their semantic tuple must be identical.
    assert first_snapshot == second_snapshot
    assert sum(1 for _version, active in second_snapshot["releases"] if active) == 1

    db = SessionLocal()
    try:
        assert db.query(ContentItem).count() == 125
        assert db.query(ContentItem).filter(ContentItem.version == "HIMMA-CONTENT-1.0").count() == 105
        assert db.query(ContentItem).filter(ContentItem.version == "HIMMA-REINFORCEMENT-ADD-1.0").count() == 18
        assert db.query(ContentItem).filter(ContentItem.version == "HIMMA-REINFORCEMENT-ADD-2.0").count() == 2
    finally:
        db.close()
