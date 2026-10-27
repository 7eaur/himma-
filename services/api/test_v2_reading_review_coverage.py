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
