"""Regressions for Student Experience v2 semantics after canonical consolidation.

Student Experience v2 remains an approved historical decision source, but its DB
overlay markers are no longer runtime authority. These tests prove the decisions
survive in the single canonical release/publisher instead of requiring a second
repair seed.
"""
from __future__ import annotations

import seed_all
from content_runtime import canonical_id, item_assets, step_assets
from db.database import SessionLocal
from db.models import ContentItem, Skill


def _item(db, canonical: str) -> ContentItem:
    matches = [item for item in db.query(ContentItem).all() if canonical_id(item) == canonical]
    assert len(matches) == 1, f"expected one {canonical}, found {len(matches)}"
    return matches[0]


def test_canonical_release_is_authoritative_for_all_125_runtime_items():
    result = seed_all.run_seed_all()
    assert result["total_items"] == 125
    assert result["canonical_release_items"] == 125
    assert result["db_runtime_items"] == 125
    assert result["pretest_experience_items"] == 30
    assert result["learning_experience_items"] == 65
    assert result["posttest_experience_items"] == 30

    db = SessionLocal()
    try:
        items = db.query(ContentItem).all()
        assert len(items) == 125
        release_versions = {
            str((item.template_data or {}).get("canonical_release_version") or "")
            for item in items
        }
        release_shas = {
            str((item.template_data or {}).get("canonical_release_sha256") or "")
            for item in items
        }
        projection_shas = {
            str((item.template_data or {}).get("canonical_projection_sha256") or "")
            for item in items
        }
        assert len(release_versions) == 1
        assert len(release_shas) == 1 and len(next(iter(release_shas))) == 64
        assert len(projection_shas) == 1 and len(next(iter(projection_shas))) == 64
    finally:
        db.close()


def test_onset_comparison_uses_approved_two_word_auditory_contract_without_overlay():
    seed_all.run_seed_all()
    db = SessionLocal()
    try:
        item = _item(db, "L1-CORE-06")
        data = item.template_data or {}
        assert data.get("canonical_interaction_type") == "listen_choose_one"
        assert "onset_pair_compare" not in data
        assert "onset_pair_version" not in data
        assert "student_experience_version" not in data

        expected = [
            (("موز", "ماء"), ("WRD-29", "WRD-11"), "الصوت نفسه"),
            (("باب", "بطة"), ("WRD-03", "WRD-12"), "الصوت نفسه"),
            (("قلم", "كرة"), ("WRD-04", "WRD-10"), "صوتان مختلفان"),
            (("سمك", "شمس"), ("WRD-05", "WRD-07"), "صوتان مختلفان"),
            (("نور", "نخلة"), ("WRD-15", "WRD-09"), "الصوت نفسه"),
        ]
        steps = sorted(item.steps, key=lambda step: step.order_index)
        assert len(steps) == len(expected)

        learning = data.get("learning_experience") or {}
        learning_rounds = sorted(learning.get("rounds") or [], key=lambda row: row["round_number"])
        assert len(learning_rounds) == len(expected)

        for step, projection, (words, asset_ids, answer) in zip(steps, learning_rounds, expected, strict=True):
            assert step.prompt_text == "هل تبدأ الكلمتان بالصوت نفسه أم بصوتين مختلفين؟"
            options = sorted(step.options, key=lambda option: option.order_index)
            assert [option.text for option in options] == ["الصوت نفسه", "صوتان مختلفان"]
            assert next(option.text for option in options if option.is_correct) == answer
            audio_assets = [
                asset for asset in step_assets(item, step)
                if asset["asset_type"] == "audio" and asset["usage"] == "prompt"
            ]
            assert tuple(asset["semantic_text"] for asset in audio_assets) == words
            assert tuple(asset["asset_id"] for asset in audio_assets) == asset_ids
            assert projection["stimulus"] == {"kind": "audio_sequence", "audio_targets": list(words)}
            assert projection["stimulus_text"] == ""
    finally:
        db.close()


def test_path_tasks_are_replaced_by_auditory_story_contract_without_runtime_patch():
    seed_all.run_seed_all()
    db = SessionLocal()
    try:
        auditory_skill = db.query(Skill).filter(
            Skill.level_id == 1,
            Skill.canonical_skill_id == "auditory_literal_comprehension",
        ).one()
        assert auditory_skill.name == "الفهم السمعي المباشر"
        assert db.query(Skill).filter(Skill.canonical_skill_id == "visual_motor_direction").count() == 0

        expected = {
            "L1-CORE-09": ("INS-01", "أين ذهبت ليان؟", ["إلى المزرعة", "إلى المدرسة", "إلى السوق", "إلى الحديقة"]),
            "L1-REIN-11": ("INS-02", "أين ذهب نادر؟", ["إلى الشاطئ", "إلى المزرعة", "إلى المدرسة"]),
        }
        for canonical, (audio_asset_id, first_question, first_options) in expected.items():
            item = _item(db, canonical)
            data = item.template_data or {}
            assert item.skill_id == auditory_skill.id
            assert item.skill.canonical_skill_id == "auditory_literal_comprehension"
            assert data.get("canonical_interaction_type") == "listen_choose_one"
            assert "auditory_story" not in data
            assert "student_experience_version" not in data

            # Story audio is intro-only. Question rounds never replay the story.
            story_assets = [asset for asset in item_assets(item) if asset["asset_type"] == "audio"]
            assert [asset["asset_id"] for asset in story_assets] == [audio_asset_id]
            assert len(item.steps) == 5
            for step in item.steps:
                assert not [asset for asset in step_assets(item, step) if asset["asset_type"] == "audio"]

            first = sorted(item.steps, key=lambda step: step.order_index)[0]
            assert first.prompt_text == first_question
            options = sorted(first.options, key=lambda option: option.order_index)
            assert [option.text for option in options] == first_options
            assert sum(1 for option in options if option.is_correct) == 1

            approval = data.get("content_approval_2026_09_08") or {}
            intro = approval.get("context_intro") or {}
            assert intro.get("kind") == "audio_story"
            assert intro.get("audio_asset_id") == audio_asset_id

        retired = [
            canonical_id(item)
            for item in db.query(ContentItem).all()
            if (item.template_data or {}).get("canonical_interaction_type") == "path_sequence"
        ]
        assert retired == []
    finally:
        db.close()


def test_post_q14_image_and_target_word_are_coherent_in_canonical_contract():
    seed_all.run_seed_all()
    db = SessionLocal()
    try:
        item = _item(db, "POST-Q14")
        data = item.template_data or {}
        assert data.get("canonical_interaction_type") == "build_word"
        step = sorted(item.steps, key=lambda value: value.order_index)[0]
        options = sorted(step.options, key=lambda option: option.order_index)
        assert [option.text for option in options] == ["ن", "خ", "ل", "ة"]

        presentation = data.get("posttest_experience") or {}
        stimulus = presentation.get("stimulus") or {}
        assert stimulus.get("kind") == "image"
        assets = [asset for asset in step_assets(item, step) if asset["asset_type"] == "image"]
        assert len(assets) == 1
        assert assets[0]["semantic_text"] == "نخلة"
    finally:
        db.close()
