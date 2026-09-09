"""DB/runtime proof that the two-word onset comparison reaches the learner intact."""

import seed_all
from content_runtime import canonical_id
from content_student_view import activity_student_content
from db.database import SessionLocal
from db.models import ContentItem

EXPECTED = [
    (("WRD-29", "WRD-11"), ("موز", "ماء")),
    (("WRD-03", "WRD-12"), ("باب", "بطة")),
    (("WRD-04", "WRD-10"), ("قلم", "كرة")),
    (("WRD-05", "WRD-07"), ("سمك", "شمس")),
    (("WRD-15", "WRD-09"), ("نور", "نخلة")),
]


def test_onset_pair_runtime_exposes_two_ordered_audio_assets_per_round():
    result = seed_all.run_seed_all()
    assert result["total_items"] == 125

    db = SessionLocal()
    try:
        item = next(
            value for value in db.query(ContentItem).all()
            if canonical_id(value) == "L1-CORE-06"
        )
        steps = sorted(item.steps, key=lambda value: value.order_index)
        assert len(steps) == 5

        for step, (asset_ids, semantics) in zip(steps, EXPECTED, strict=True):
            payload = activity_student_content(item, step)
            assert payload["step"]["question_text"] == "هل تبدأ الكلمتان بالصوت نفسه أم بصوتين مختلفين؟"
            assert payload["step"]["instruction_text"] == "استمع إلى الكلمتين كاملتين، ثم قارن أول صوت في كل كلمة."
            assert payload["step"]["stimulus"] == {
                "kind": "audio_sequence",
                "audio_targets": list(semantics),
            }
            audio = [
                asset for asset in payload["step"]["assets"]
                if asset["asset_type"] == "audio" and asset["usage"] == "prompt"
            ]
            assert tuple(asset["asset_id"] for asset in audio) == asset_ids
            assert tuple(asset["semantic_text"] for asset in audio) == semantics
            assert tuple(asset["url"] for asset in audio) == tuple(
                f"/api/media/{asset_id}" for asset_id in asset_ids
            )
    finally:
        db.close()
