"""Read-only V2 reading result contracts; no Azure credentials or child audio."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select

from db.v2_reading_models import V2ReadingEvaluation, V2ReadingJob
from test_v2_reading_job_store import db, enqueue_assessment, new_v2_assessment
from v2_reading_engine.job_store import ReadingConflict
from v2_reading_engine.read_models import (
    student_reading_status, supervisor_reading_results, supervisor_audio_binding,
)


def seeded(db):
    student, release, response, audio = new_v2_assessment(db)
    job = enqueue_assessment(db, student, release, response, audio)
    db.flush()
    return student, release, response, audio, job


def test_student_only_sees_owned_current_job_and_safe_processing_state(db):
    student, release, response, audio, job = seeded(db)
    result = student_reading_status(db, job_id=job.id, student_id=student.id)
    assert result == {
        "state": "processing", "message": "نستمع إلى قراءتك...",
        "retry_required": False,
    }
    with pytest.raises(ReadingConflict):
        student_reading_status(db, job_id=job.id, student_id=student.id + 1)
    with pytest.raises(ReadingConflict):
        student_reading_status(db, job_id=job.id + 999, student_id=student.id)


@pytest.mark.parametrize("technical,ui_state,retry,phrase", [
    ("queued", "processing", False, "نستمع"),
    ("processing", "processing", False, "نستمع"),
    ("retry_wait", "processing", False, "نستمع"),
    ("evidence_ready", "processing", False, "نستمع"),
    ("retry_audio", "retry_audio", True, "جرّب"),
    ("service_unavailable", "unavailable", False, "تسجيلك محفوظ"),
])
def test_student_status_has_no_provider_or_academic_penalty(
    db, technical, ui_state, retry, phrase,
):
    student, release, response, audio, job = seeded(db)
    job.status = technical
    result = student_reading_status(db, job_id=job.id, student_id=student.id)
    assert result["state"] == ui_state
    assert result["retry_required"] is retry
    assert phrase in result["message"]
    assert not (set(result) - {"state", "message", "retry_required"})


def test_assessment_result_hides_correctness_even_after_success(db):
    student, release, response, audio, job = seeded(db)
    job.status = "applied"
    db.add(V2ReadingEvaluation(
        job_id=job.id, audio_submission_id=audio.id,
        decision="incorrect", score_fraction=Decimal("0.85"),
        passed_for_progress=False,
        evidence_json={"transcript": "wrong", "matched_alias": "例", "reason": "mismatch"},
    ))
    db.flush()
    result = student_reading_status(db, job_id=job.id, student_id=student.id)
    assert result == {
        "state": "completed",
        "message": "تم تسجيل قراءتك. نكمل السؤال التالي.",
        "retry_required": False,
    }
    assert not any(x in repr(result).lower() for x in ("azure", "例", "wrong", "0.85", "score"))


def test_training_incorrect_result_returns_teaching_hint_without_raw_asr(db):
    student, release, response, audio, job = seeded(db)
    job.learning_mode = "training"
    job.status = "applied"
    db.add(V2ReadingEvaluation(
        job_id=job.id, audio_submission_id=audio.id,
        decision="incorrect", score_fraction=Decimal("0"),
        passed_for_progress=False,
        evidence_json={"training_hint": "نسيت كلمة «مكتبة». اقرأ العبارة مرة أخرى.",
                       "matched_alias": "ل", "transcript": "raw provider transcript"},
    ))
    db.flush()
    result = student_reading_status(db, job_id=job.id, student_id=student.id)
    assert result["state"] == "incorrect"
    # Recognized but wrong: show a training hint, not an unclear-audio retry.
    assert result["retry_required"] is False
    assert "نسيت كلمة" in result["hint"]
    assert "matched_alias" not in result and "transcript" not in result


def test_staff_results_are_paginated_and_tell_only_educational_information(db):
    student, release, response, audio, job = seeded(db)
    job.status = "applied"
    job.reading_kind = "sentence"
    db.add(V2ReadingEvaluation(
        job_id=job.id, audio_submission_id=audio.id,
        decision="correct", score_fraction=Decimal("0.85714"),
        passed_for_progress=True,
        evidence_json={"transcript": "not for staff default", "matched_alias": "la"},
    ))
    db.flush()
    view = supervisor_reading_results(db, limit=1, offset=0, state="completed")
    assert view["total"] == 1 and view["next_offset"] is None
    item = view["items"][0]
    assert item["student_id"] == student.id
    assert item["result"] == "صحيحة"
    assert item["reference"] == "لَ"
    assert item["score_percent"] == 85.714
    assert not any(k in item for k in ("transcript", "matched_alias", "provider", "secret"))
    assert supervisor_reading_results(db, state="needs_attention")["items"] == []


def test_unavailable_and_retry_count_as_staff_attention(db):
    student, release, response, audio, job = seeded(db)
    job.status = "retry_audio"
    result = supervisor_reading_results(db, state="needs_attention")
    assert result["total"] == 1
    assert result["items"][0]["result"] == "إعادة تسجيل مطلوبة"


def test_private_audio_binding_rejects_substituted_key_and_old_job(db):
    student, release, response, audio, job = seeded(db)
    assert supervisor_audio_binding(db, job_id=job.id) == (
        audio.storage_key, student.id,
    )
    audio.storage_key = "audio/another-child/recording.wav"
    with pytest.raises(ReadingConflict):
        supervisor_audio_binding(db, job_id=job.id)
    audio.storage_key = f"audio/{student.id}/recording.wav"
    job.is_current = False
    with pytest.raises(ReadingConflict):
        supervisor_audio_binding(db, job_id=job.id)


def test_staff_filter_pagination_input_rejected(db):
    seeded(db)
    with pytest.raises(ValueError):
        supervisor_reading_results(db, limit=0)
    with pytest.raises(ValueError):
        supervisor_reading_results(db, offset=-1)
    with pytest.raises(ValueError):
        supervisor_reading_results(db, state="unknown")


def test_supervisor_search_matches_student_name_or_question_with_pagination(db):
    student, release, response, audio, job = seeded(db)
    by_name = supervisor_reading_results(db, search="Learner")
    assert by_name["total"] == 1
    assert by_name["items"][0]["student_id"] == student.id
    by_question = supervisor_reading_results(db, search="V2-PRE-Q06")
    assert by_question["total"] == 1
    assert supervisor_reading_results(db, search="not-an-existing-student")["total"] == 0
    assert supervisor_reading_results(db, search="%")["total"] == 0
    with pytest.raises(ValueError):
        supervisor_reading_results(db, search="a" * 81)



def test_final_incorrect_focused_support_audio_displays_reading_model_only_after_three(db):
    """Only fully graded focused support, not normal lessons or tests, may show it."""
    from db.learning_models import LessonSession, LessonQuestionResponse, SupportAssignment
    from db.models import AudioSubmission
    from v2_reading_engine.job_store import enqueue_reading
    student, release, _answer, _audio = new_v2_assessment(db)
    lesson = LessonSession(
        student_id=student.id, content_release_id=release.id,
        lesson_id="L1-04", stage="support_check", status="in_progress",
        step_index=0,
    )
    db.add(lesson)
    db.flush()
    assignment = SupportAssignment(
        lesson_session_id=lesson.id, student_id=student.id,
        content_release_id=release.id, support_id="SUP-03",
        focus="letters", target_skill="S3",
        source_lesson_id="L1-04", source_level=1, support_level=1,
        mode="targeted_support", status="active",
        verification_round=0, practice_question_ids=["SUP-03-GP-01"],
        check_question_ids=["SUP-03-SC-01"],
        return_to={"lesson_id": "L1-04"}, policy_version="test",
    )
    db.add(assignment)
    db.flush()

    def make_result(*, attempt_no: int, use_support: bool):
        response = LessonQuestionResponse(
            lesson_session_id=lesson.id,
            question_id="SUP-03-GP-01" if use_support else "L1-04-GP-02",
            role="guided_practice", answer_json={},
            submit_key=f"take-{attempt_no}-{use_support}",
            attempt_no=attempt_no, status="graded", is_correct=False,
            support_assignment_id=assignment.id if use_support else None,
        )
        db.add(response)
        db.flush()
        audio = AudioSubmission(
            lesson_response_id=response.id,
            storage_key=f"audio/{student.id}/take-{response.id}.wav",
            file_size=3000, mime_type="audio/wav", status="graded",
        )
        db.add(audio)
        db.flush()
        job = enqueue_reading(
            db, student_id=student.id, audio_submission_id=audio.id,
            content_release_id=release.id, question_id=response.question_id,
            reference_text="سُ" if use_support else "رَ",
            reading_kind="letter", learning_mode="training",
        )
        job.status = "applied"
        db.add(V2ReadingEvaluation(
            job_id=job.id, audio_submission_id=audio.id,
            decision="incorrect", score_fraction=Decimal("0"),
            passed_for_progress=False, evidence_json={
                "training_hint": "اقرأ الحرف مرة أخرى.",
                "transcript": "مختلف",
            },
        ))
        db.flush()
        return student_reading_status(db, job_id=job.id, student_id=student.id)

    second = make_result(attempt_no=2, use_support=True)
    assert second["state"] == "incorrect"
    assert second["retry_required"] is False
    assert "model_text" not in second and "assisted_advance" not in second

    third = make_result(attempt_no=3, use_support=True)
    assert third["state"] == "incorrect"
    assert third["assisted_advance"] is True
    assert third["model_text"] == "سُ"
    assert third["retry_required"] is False
    assert "transcript" not in third
    assert "provider" not in third

    ordinary = make_result(attempt_no=3, use_support=False)
    assert ordinary["state"] == "incorrect"
    assert "model_text" not in ordinary and "assisted_advance" not in ordinary

    for item in (second, third, ordinary):
        assert "transcript" not in item and "matched_alias" not in item
