"""P08 gate: every authored reading question is owned by safe human review."""
from v2_content.contracts import PRIVATE_KEYS
from v2_content.projection import student_question
from v2_content.repository import get_release


def _keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _keys(item)
    elif isinstance(value, list):
        for child in value:
            yield from _keys(child)


def test_all_62_reading_items_have_private_human_rubrics_and_no_student_answer_leak():
    questions = get_release()["questions"]
    reading = [q for q in questions if q["interaction"] == "read_aloud"]
    assert len(questions) == 300
    assert len(reading) == 62
    assert {q["role"] for q in reading} == {
        "guided_practice", "independent_check", "support_check", "pretest", "posttest",
    }
    assert len({q["id"] for q in reading}) == 62
    for question in reading:
        assert question.get("stimulus", {}).get("text"), question["id"]
        rubric = question.get("private_answer", {}).get("rubric")
        assert isinstance(rubric, dict) and rubric, question["id"]
        assert not question["private_answer"]["correct_option_ids"], question["id"]
        assert (
            rubric.get("authority") == "human_supervisor"
            or rubric.get("evaluation_authority") == "human_supervisor"
        ), question["id"]
        assert (
            rubric.get("reference")
            or rubric.get("reference_text")
            or rubric.get("target_or_reference")
        ), question["id"]
        student = student_question(question)
        keys = set(_keys(student))
        assert not PRIVATE_KEYS.intersection(keys), question["id"]
        assert "rubric" not in keys, question["id"]
        assert "correct_option_ids" not in keys, question["id"]


def test_all_recording_questions_request_direct_reading_of_the_visible_target():
    """Learners see the full target once; no mandatory segmentation or blending."""
    import re

    reading = [q for q in get_release()["questions"] if q["interaction"] == "read_aloud"]
    expected_prompts = {
        "letter": "اقرأ الحرف بصوت واضح.",
        "word": "اقرأ الكلمة بصوت واضح.",
        "sentence": "اقرأ الجملة بصوت واضح.",
        "two_sentences": "اقرأ الجملتين بصوت واضح.",
        "text": "اقرأ النص بصوت واضح.",
    }
    categories = {category: 0 for category in expected_prompts}
    by_id = {q["id"]: q for q in reading}
    for question in reading:
        target = question["stimulus"]["text"]
        assert target and "+" not in target, question["id"]
        plain = re.sub(r"[\u064b-\u065f\u0670]", "", target).strip()
        sentences = target.count(".")
        if sentences >= 3:
            category = "text"
        elif sentences == 2:
            category = "two_sentences"
        elif sentences == 1:
            category = "sentence"
        elif len(plain) == 1:
            category = "letter"
        else:
            category = "word"
        categories[category] += 1
        assert question["prompt"] == expected_prompts[category], question["id"]
        hint = question.get("hint") or ""
        assert not any(
            part in hint for part in ("اجمع", "ادمج", "أجزاء", "جزء", "قسّم", "قسم النص")
        ), question["id"]
        assert question["student_presentation"]["student_input"] == "voice_recording", question["id"]

    assert categories == {
        "letter": 10, "word": 22, "sentence": 9,
        "two_sentences": 11, "text": 10,
    }
    for question_id, expected in {
        "L1-05-GP-04": "نَزَلَ",
        "L1-05-IC-A03": "رَكَبَ",
    }.items():
        question = by_id[question_id]
        assert question["stimulus"]["text"] == expected
        assert question["reading_reference"] == expected
        assert question["private_answer"]["rubric"]["reference_text"] == expected
