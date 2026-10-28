from uuid import uuid4

import pytest

from conftest import TestingSessionLocal
from db.learning_models import LessonQuestionDraft, LessonQuestionResponse, LessonSession, StudentJourney
from db.models import AudioSubmission, Student
from v2_content.compiler import compile_release
from v2_content.contracts import PRIVATE_KEYS
from v2_content.importer import register_candidate_release
from test_v2_lesson_runtime import _place_fixture


def _start_at_questions(student_client, lesson_id: str, step_index: int = 0):
    # Component/runtime coverage deliberately opens representative questions
    # from all levels. Seed the authoritative current lesson instead of
    # weakening the production route's lesson-lock check.
    _place_fixture(level=int(lesson_id[1]), cursor=lesson_id)
    started_response = student_client.post(f"/v2/lessons/{lesson_id}/start")
    assert started_response.status_code == 200, started_response.text
    started = started_response.json()
    session_id = started["session"]["session_id"]
    student_client.post(
        f"/v2/lessons/sessions/{session_id}/events",
        json={"event_key": str(uuid4()), "event_type": "intro_complete"},
    )
    student_client.post(
        f"/v2/lessons/sessions/{session_id}/events",
        json={
            "event_key": str(uuid4()),
            "event_type": "video_ended",
            "position_seconds": 6,
            "duration_seconds": 6,
        },
    )
    if step_index:
        with TestingSessionLocal() as db:
            session = db.query(LessonSession).filter(LessonSession.id == session_id).one()
            session.step_index = step_index
            db.commit()
    return session_id


def _all_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _all_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _all_keys(child)


@pytest.mark.parametrize(
    ("lesson_id", "step_index", "interaction"),
    [
        ("L1-01", 0, "listen_choose_one"),
        ("L1-01", 1, "choose_one"),
        ("L1-05", 0, "sequence"),
        ("L2-01", 0, "build_word"),
        ("L1-06", 3, "choose_image"),
        ("L1-05", 3, "read_aloud"),
        ("L2-01", 3, "build_word"),
    ],
)
def test_current_bank_interactions_share_one_safe_runtime(student_client, lesson_id, step_index, interaction):
    session_id = _start_at_questions(student_client, lesson_id, step_index)
    response = student_client.get(f"/v2/lessons/sessions/{session_id}/interaction")
    assert response.status_code == 200
    payload = response.json()["interaction"]
    assert payload["question"]["interaction"] == interaction
    assert PRIVATE_KEYS.isdisjoint(set(_all_keys(payload)))
    assert "correct_option_ids" not in set(_all_keys(payload))


def test_guided_feedback_retries_without_leaking_and_submit_key_replays(student_client):
    session_id = _start_at_questions(student_client, "L1-01")
    key = str(uuid4())
    wrong = {"submit_key": key, "selected_option_ids": ["b"]}
    first = student_client.post(f"/v2/lessons/sessions/{session_id}/answers", json=wrong)
    assert first.status_code == 200
    assert first.json()["submission"]["correct"] is False
    assert first.json()["submission"]["retry_required"] is True
    assert first.json()["lesson"]["interaction"]["question"]["question_id"] == "L1-01-GP-01"
    assert "correct_option_ids" not in set(_all_keys(first.json()))

    replay = student_client.post(f"/v2/lessons/sessions/{session_id}/answers", json=wrong)
    assert replay.status_code == 200
    assert replay.json()["status"] == "replayed"
    conflict = student_client.post(
        f"/v2/lessons/sessions/{session_id}/answers",
        json={"submit_key": key, "selected_option_ids": ["a"]},
    )
    assert conflict.status_code == 409

    correct = student_client.post(
        f"/v2/lessons/sessions/{session_id}/answers",
        json={"submit_key": str(uuid4()), "selected_option_ids": ["a"]},
    )
    assert correct.status_code == 200
    assert correct.json()["submission"]["correct"] is True
    assert correct.json()["lesson"]["interaction"]["progress"]["index"] == 2


def test_independent_check_never_returns_correctness_or_hint(student_client):
    session_id = _start_at_questions(student_client, "L1-01")
    with TestingSessionLocal() as db:
        session = db.query(LessonSession).filter(LessonSession.id == session_id).one()
        session.stage = "independent_check"
        session.step_index = 0
        db.commit()
    response = student_client.post(
        f"/v2/lessons/sessions/{session_id}/answers",
        json={"submit_key": str(uuid4()), "selected_option_ids": ["c"]},
    )
    assert response.status_code == 200
    submission = response.json()["submission"]
    assert "correct" not in submission
    assert "hint" not in submission
    assert submission["message"] == "تم حفظ إجابتك."
    assert response.json()["lesson"]["interaction"]["progress"]["index"] == 2


def test_word_builder_auto_grades_without_human_review(student_client):
    from v2_content.repository import get_question

    session_id = _start_at_questions(student_client, "L2-01", 3)
    item = student_client.get(f"/v2/lessons/sessions/{session_id}/interaction").json()["interaction"]
    assert item["question"]["interaction"] == "build_word"
    assert "correct_option_ids" not in set(_all_keys(item))
    assert student_client.put(
        f"/v2/lessons/sessions/{session_id}/draft", json={"text": "باب"}
    ).status_code == 404

    question = get_question("L2-01-GP-04")
    submitted = student_client.post(
        f"/v2/lessons/sessions/{session_id}/answers",
        json={"submit_key": str(uuid4()), "selected_option_ids": question["private_answer"]["correct_option_ids"]},
    )
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["submission"]["status"] == "graded"
    assert submitted.json()["submission"]["correct"] is True
    with TestingSessionLocal() as db:
        response = db.query(LessonQuestionResponse).one()
        assert response.is_correct is True and response.status == "graded"
        assert db.query(LessonQuestionDraft).count() == 0


def test_reading_upload_reuses_private_storage_and_is_academically_neutral(student_client, monkeypatch):
    session_id = _start_at_questions(student_client, "L1-05", 3)
    monkeypatch.setattr(
        "v2_interaction_runtime.storage.upload_audio",
        lambda _file, student_id, _idempotency_key: (
            f"audio/{student_id}/test-v2-reading.webm",
            2048,
            "digest",
        ),
    )
    monkeypatch.setattr("v2_interaction_runtime.storage.verify_audio", lambda *args, **kwargs: None)
    upload = student_client.post(
        f"/v2/lessons/sessions/{session_id}/recording",
        headers={"Idempotency-Key": str(uuid4())},
        files={"file": ("reading.webm", b"audio-bytes", "audio/webm")},
    )
    assert upload.status_code == 200
    submitted = student_client.post(
        f"/v2/lessons/sessions/{session_id}/answers",
        json={
            "submit_key": str(uuid4()),
            **upload.json(),
            "audio_duration_seconds": 3,
        },
    )
    assert submitted.status_code == 200
    assert submitted.json()["submission"]["status"] == "pending_review"
    with TestingSessionLocal() as db:
        response = db.query(LessonQuestionResponse).one()
        recording = db.query(AudioSubmission).one()
        assert response.is_correct is None
        assert recording.lesson_response_id == response.id
        assert recording.response_id is None
        assert recording.status == "pending_review"


def test_original_snapshot_survives_current_bank_change_for_lesson_interaction(student_client, monkeypatch):
    session_id = _start_at_questions(student_client, "L1-01")
    initial = student_client.get(f"/v2/lessons/sessions/{session_id}/interaction")
    assert initial.status_code == 200, initial.text
    original = initial.json()["interaction"]["question"]["question_id"]

    # The student's immutable release was stored before changing authoring.
    monkeypatch.setattr("v2_content.repository.get_release",
                        lambda: {"version": "later-authoring", "checksum": "different"})
    resumed = student_client.get(f"/v2/lessons/sessions/{session_id}/interaction")
    assert resumed.status_code == 200, resumed.text
    assert resumed.json()["interaction"]["question"]["question_id"] == original
