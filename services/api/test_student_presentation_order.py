"""Regression coverage for learner-visible option/media ordering.

Academic order remains durable in PostgreSQL for scoring, especially sequence and
build-word tasks. These tests lock the separate presentation order shared by live
assessment, live learning and researcher preview so image grids cannot reveal the
canonical answer order by accident.
"""
from __future__ import annotations

from types import SimpleNamespace

import seed_all
from content_runtime import canonical_id
from content_student_view import (
    _align_choice_assets,
    activity_student_content,
    assessment_student_payload,
    presented_options,
)
from db.database import SessionLocal
from db.models import ContentItem


def _option(option_id: int, order_index: int):
    return SimpleNamespace(
        id=option_id,
        order_index=order_index,
        text=f"خيار {order_index}",
        is_correct=order_index == 1,
        is_active=True,
    )


def test_presentation_order_is_deterministic_and_separate_from_academic_order():
    step = SimpleNamespace(options=[
        _option(10, 1),
        _option(11, 2),
        _option(12, 3),
        _option(13, 4),
    ])

    first = presented_options(step)
    second = presented_options(step)

    assert [value.id for value in first] == [12, 13, 10, 11]
    assert [value.id for value in second] == [12, 13, 10, 11]
    # The durable scoring order is untouched.
    assert [value.id for value in step.options] == [10, 11, 12, 13]
    assert [value.order_index for value in step.options] == [1, 2, 3, 4]


def test_choice_images_follow_presented_option_ids_without_moving_prompt_audio():
    options = [_option(12, 3), _option(13, 4), _option(10, 1), _option(11, 2)]
    assets = [
        {"asset_id": "LET-01", "asset_type": "audio", "usage": "prompt", "option_id": None},
        {"asset_id": "IMG-10", "asset_type": "image", "usage": "choice", "option_id": 10},
        {"asset_id": "IMG-11", "asset_type": "image", "usage": "choice", "option_id": 11},
        {"asset_id": "IMG-12", "asset_type": "image", "usage": "choice", "option_id": 12},
        {"asset_id": "IMG-13", "asset_type": "image", "usage": "choice", "option_id": 13},
    ]

    aligned = _align_choice_assets(assets, options)

    assert aligned[0]["asset_id"] == "LET-01"
    assert [value["option_id"] for value in aligned[1:]] == [12, 13, 10, 11]


def test_all_seeded_student_payloads_keep_mapped_image_order_equal_to_option_presentation():
    result = seed_all.run_seed_all()
    assert result["total_items"] == 125

    db = SessionLocal()
    try:
        for item in db.query(ContentItem).all():
            for step in sorted(item.steps, key=lambda value: value.order_index):
                if item.kind in {"pretest_question", "posttest_question"}:
                    payload = assessment_student_payload(item, step)["steps"][0]
                else:
                    payload = activity_student_content(item, step)["step"]

                option_ids = [int(option["id"]) for option in payload["options"]]
                mapped = [
                    int(asset["option_id"])
                    for asset in payload["assets"]
                    if asset.get("asset_type") == "image" and asset.get("option_id") is not None
                ]
                if not mapped:
                    continue

                expected = [option_id for option_id in option_ids if option_id in set(mapped)]
                assert mapped == expected, (canonical_id(item), step.order_index, mapped, expected)
    finally:
        db.close()
