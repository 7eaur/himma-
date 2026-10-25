"""Regression gate for the 21 owner-approved, automatically graded tile questions."""
from uuid import uuid4

from conftest import TestingSessionLocal
from db.learning_models import AssessmentQuestionResponse
from db.models import AssessmentSession
from v2_content.compiler import compile_release
from v2_content.projection import student_question
from v2_interaction_runtime import _ordered_answer_is_correct


def _all_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _all_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _all_keys(child)


def test_every_converted_item_has_private_valid_options_and_auto_grading():
    release = compile_release()
    questions = release["questions"]
    assert len(questions) == 300
    assert release["counts"]["interactions"] == {
        "choose_one": 107,
        "listen_choose_one": 52,
        "choose_image": 4,
        "sequence": 57,
        "build_word": 18,
        "read_aloud": 62,
    }
    converted = [q for q in questions if q["private_answer"].get("scoring") == "ordered_option_ids_exact"]
    assert len(converted) == 21
    assert sum(q["interaction"] == "build_word" for q in converted) == 9
    assert sum(q["interaction"] == "sequence" for q in converted) == 12
    assert all(q["interaction"] != "write_text" for q in questions)
    for q in converted:
        option_map = {option["id"]: option["text"] for option in q["options"]}
        assert len(option_map) == len(q["options"])
        answer = q["private_answer"]
        expected = answer["correct_option_ids"]
        assert len(expected) == len(option_map)
        assert set(expected) == set(option_map)
        sep = "" if q["interaction"] == "build_word" else " "
        assert sep.join(option_map[key] for key in expected) == answer["target_text"]
        assert [o["id"] for o in q["options"]] != expected
        assert _ordered_answer_is_correct(q, expected) is True
        assert _ordered_answer_is_correct(q, [o["id"] for o in q["options"]]) is False
        for alternative in answer.get("accepted_option_orders", []):
            assert set(alternative) == set(expected) and len(alternative) == len(expected)
            assert _ordered_answer_is_correct(q, alternative) is True
        student = student_question(q)
        keys = set(_all_keys(student))
        assert not {"private_answer", "correct_option_ids", "accepted_option_orders", "target_text"} & keys
        if q["role"] != "guided_practice":
            assert student["hint"] is None


def test_pretest_word_building_is_graded_automatically_without_reviewer(student_client):
    started = student_client.post("/v2/assessments/pretest/start")
    assert started.status_code == 200
    session_id = started.json()["session"]["session_id"]
    # Start at Q12 using test data, not by weakening the production journey.
    with TestingSessionLocal() as db:
        session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).one()
        session.v2_question_index = 11
        db.commit()
    loaded = student_client.get(f"/v2/assessments/sessions/{session_id}")
    assert loaded.status_code == 200
    assert loaded.json()["interaction"]["question"]["question_id"] == "V2-PRE-Q12"
    question = next(q for q in compile_release()["questions"] if q["id"] == "V2-PRE-Q12")
    answer = question["private_answer"]["correct_option_ids"]
    submitted = student_client.post(f"/v2/assessments/sessions/{session_id}/answers", json={
        "submit_key": str(uuid4()), "selected_option_ids": answer,
    })
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["submission"]["status"] == "graded"
    assert "correct" not in submitted.json()["submission"]
    with TestingSessionLocal() as db:
        response = db.query(AssessmentQuestionResponse).one()
        assert response.question_id == "V2-PRE-Q12"
        assert response.is_correct is True and response.status == "graded"


def test_pretest_sentence_accepts_approved_alternative_without_leaking_score(student_client):
    started = student_client.post("/v2/assessments/pretest/start")
    session_id = started.json()["session"]["session_id"]
    with TestingSessionLocal() as db:
        session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).one()
        session.v2_question_index = 29
        db.commit()
    question = next(q for q in compile_release()["questions"] if q["id"] == "V2-PRE-Q30")
    alternative = question["private_answer"]["accepted_option_orders"][0]
    response = student_client.post(f"/v2/assessments/sessions/{session_id}/answers", json={
        "submit_key": str(uuid4()), "selected_option_ids": alternative,
    })
    assert response.status_code == 200, response.text
    assert response.json()["submission"]["status"] == "graded"
    assert "correct" not in response.json()["submission"]
    with TestingSessionLocal() as db:
        recorded = db.query(AssessmentQuestionResponse).one()
        assert recorded.question_id == "V2-PRE-Q30"
        assert recorded.is_correct is True
