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
    assert result["retry_required"] is True
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
