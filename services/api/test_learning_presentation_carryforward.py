"""Regression coverage for the approved Sep-01/R2 presentation carried into Sep-08."""

from canonical_release import build_canonical_release
from content_approval_contract_2026_09_08 import LEARNING_QUESTIONS


def _by_id():
    release = build_canonical_release()
    return {item["canonical_id"]: item for item in release["items"]}


def test_sep8_questions_win_without_losing_current_instruction_or_hint():
    items = _by_id()

    visual = items["L1-CORE-01"]
    assert visual["rounds"][0]["question_text"] == LEARNING_QUESTIONS["L1-CORE-01"]
    assert visual["rounds"][0]["instruction_text"] == "انظر إلى الحرف المطلوب، ثم اختره من الحروف المعروضة."
    # R2 explicitly replaced the older answer-revealing classification wording.
    classification = items["L1-CORE-07"]["rounds"][0]
    assert classification["hint"] == "لاحظ حجم العنصر وعدد الرموز والمسافات بين أجزائه، ثم اختر التصنيف المناسب."


def test_student_v2_onset_pair_instruction_is_not_regressed_to_old_sound_word_task():
    item = _by_id()["L1-CORE-06"]
    for step in item["rounds"]:
        assert step["question_text"] == LEARNING_QUESTIONS["L1-CORE-06"]
        assert step["instruction_text"] == "استمع إلى الكلمتين كاملتين، ثم قارن أول صوت في كل كلمة."
        assert step["hint"] == "ركّز على بداية الكلمة الأولى ثم بداية الكلمة الثانية."
        assert "بداية الكلمة وقارن" not in step["instruction_text"]


def test_structurally_changed_read_aloud_uses_current_r2_reading_guidance():
    item = _by_id()["L2-REIN-07"]
    assert item["interaction_type"] == "read_aloud"
    for step in item["rounds"]:
        assert step["question_text"] == LEARNING_QUESTIONS["L2-REIN-07"]
        assert step["instruction_text"] == "اضغط زر التسجيل، اقرأ النص المعروض، ثم أرسل التسجيل."
        assert step["hint"] == "اقرأ ببطء ووضوح، وركّز في الحروف والحركات."
        assert step["options"] == []


def test_r2_projection_overrides_remain_independent_from_new_question_copy():
    item = _by_id()["L3-REIN-05"]
    for step in item["rounds"]:
        assert step["question_text"] == LEARNING_QUESTIONS["L3-REIN-05"]
        assert step["instruction_text"] == "اقرأ النص أو شاهده، ثم اختر العنوان الذي يلخص فكرته."
        assert step["hint"] == "اختر العنوان الذي يجمع الفكرة الأهم في النص."


def test_auditory_story_round_guidance_is_not_overwritten_by_retired_direction_metadata():
    item = _by_id()["L1-CORE-09"]
    assert item["canonical_skill_code"] == "auditory_literal_comprehension"
    assert item["rounds"]
    for step in item["rounds"]:
        assert step["instruction_text"] == "اختر الإجابة الصحيحة اعتمادًا على ما فهمته من القصة."
        assert "جهة القراءة" not in step["instruction_text"]
        assert "جهة اليمين" not in step["hint"]


def test_learning_encouragement_matches_approved_r2_sequence():
    item = _by_id()["L1-CORE-01"]
    assert len(item["rounds"]) == 5
    assert [step["encouragement"] for step in item["rounds"]] == [
        "ممتاز، أنت جاهز لهذه الجولة!",
        "رائع، واصل تقدمك!",
        "أحسنت، أنت تتقدم بشكل جميل!",
        "ممتاز، بقي القليل!",
        "رائع، أكمل الجولة الأخيرة بثقة!",
    ]
