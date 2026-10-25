"""P08 audio retention: replace recordings only after accepted review.

No child recording is deleted while it is still the active/pending evidence.
"""
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from conftest import TestingSessionLocal
from db.learning_models import LessonQuestionResponse, LessonSession
from db.models import AudioPurgeTask, AudioSubmission, Student
from v2_audio_retention import (
    process_queued_audio_purges, schedule_superseded_audio,
    schedule_superseded_staged_audio,
)


def _record(db, student_id, question_id, state, suffix):
    session = LessonSession(student_id=student_id, content_release_id=1, lesson_id="L1-05")
    # The caller creates a real content release; this helper is not used
    # directly in isolation to avoid missing foreign keys.
    return session


def test_graded_replacement_purges_old_binary_and_keeps_latest(monkeypatch):
    from v2_content.importer import register_candidate_release

    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        sid = student.id
        release = register_candidate_release(db)
        session = LessonSession(student_id=sid, content_release_id=release.id, lesson_id="L1-05")
        db.add(session); db.flush()
        response = LessonQuestionResponse(
            lesson_session_id=session.id, question_id="L1-05-GP-04",
            role="guided_practice", answer_json={"answer": {"audio_storage_key": f"audio/{sid}/old.webm"}},
            submit_key=str(uuid4()), status="graded", is_correct=True,
            reviewed_at=datetime.now(timezone.utc),
        )
        db.add(response); db.flush()
        old = AudioSubmission(lesson_response_id=response.id, storage_key=f"audio/{sid}/old.webm",
                              file_size=2345, mime_type="audio/webm", status="rerecord_required")
        latest = AudioSubmission(lesson_response_id=response.id, storage_key=f"audio/{sid}/final.audio",
                                 file_size=1900, mime_type="audio/mp4", status="graded")
        db.add_all([old, latest]); db.flush()
        old_id, latest_id = old.id, latest.id
        schedule_superseded_audio(db, student_id=sid, question_id=response.question_id,
                                  winning_audio_id=latest.id, kind="lesson",
                                  extra_staged_keys=(f"audio/{sid}/extra-temp.audio",))
        db.commit()
        assert db.query(AudioPurgeTask).filter(AudioPurgeTask.status == "queued").count() == 2
        assert db.query(AudioSubmission).filter(AudioSubmission.id == latest_id).one().status == "graded"

    deleted_keys = []
    monkeypatch.setattr("v2_audio_retention.SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("v2_audio_retention.storage.delete_superseded_audio",
                        lambda key, owner: deleted_keys.append((key, owner)))
    results = process_queued_audio_purges()
    assert results == {"deleted": 2, "deferred": 0}
    assert set(deleted_keys) == {
        (f"audio/{sid}/old.webm", sid),
        (f"audio/{sid}/extra-temp.audio", sid),
    }
    with TestingSessionLocal() as db:
        archived = db.query(AudioSubmission).filter(AudioSubmission.id == old_id).one()
        retained = db.query(AudioSubmission).filter(AudioSubmission.id == latest_id).one()
        assert archived.status == "purged" and archived.storage_key == f"purged/{old_id}"
        assert retained.status == "graded" and retained.storage_key == f"audio/{sid}/final.audio"
        assert all(task.storage_key is None for task in db.query(AudioPurgeTask).all())
    assert process_queued_audio_purges()["deleted"] == 0


def test_never_delete_current_sound_when_a_second_take_is_not_graded():
    from v2_content.importer import register_candidate_release

    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        session = LessonSession(student_id=student.id, content_release_id=release.id, lesson_id="L1-05")
        db.add(session); db.flush()
        response = LessonQuestionResponse(
            lesson_session_id=session.id, question_id="L1-05-GP-04",
            role="guided_practice", answer_json={"answer": {"audio_storage_key": f"audio/{student.id}/old.webm"}},
            submit_key=str(uuid4()), status="pending_review",
        )
        db.add(response); db.flush()
        audio = AudioSubmission(lesson_response_id=response.id, storage_key=f"audio/{student.id}/old.webm",
                                file_size=2345, mime_type="audio/webm", status="pending_review")
        db.add(audio); db.flush()
        with pytest.raises(ValueError, match="accepted"):
            schedule_superseded_audio(db, student_id=student.id,
                                      question_id=response.question_id,
                                      winning_audio_id=audio.id, kind="lesson")
        assert db.query(AudioPurgeTask).count() == 0


def test_staged_cleanup_rejects_foreign_student_and_preserves_evidence(monkeypatch):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        with pytest.raises(ValueError, match="ownership"):
            schedule_superseded_staged_audio(db, student_id=student.id, keys=("audio/9999/foreign.webm",))
        db.rollback()
        schedule_superseded_staged_audio(db, student_id=student.id,
                                         keys=(f"audio/{student.id}/unused.webm",))
        db.commit()
    monkeypatch.setattr("v2_audio_retention.SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("v2_audio_retention.storage.delete_superseded_audio",
                        lambda *_: (_ for _ in ()).throw(RuntimeError("S3 down")))
    assert process_queued_audio_purges()["deferred"] == 1
    with TestingSessionLocal() as db:
        assert db.query(AudioPurgeTask).filter(AudioPurgeTask.status == "queued").count() == 1
