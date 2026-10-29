"""V2 supervisor review: recorded reading only, private and auditable."""
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError
from conftest import TestingSessionLocal
from db.learning_models import (
    LessonQuestionResponse, SkillEvidence, V2LessonReviewAction,
    LessonSession, V2ReviewRetryTask, AdaptationDecision, PrivateContentBankSnapshot,
)
from db.models import Student
from test_v2_interaction_runtime import _start_at_questions


def login_staff(client):
    assert client.post("/auth/login", json={
        "username": "researcher1", "password": "test-only-researcher-password",
    }).status_code == 200


def login_student(client, code="STU001"):
    assert client.post("/auth/student-login", json={"access_code": code}).status_code == 200


def reading(client, monkeypatch, filename="original"):
    import storage
    monkeypatch.setattr(storage, "verify_audio", lambda *a, **kw: None)
    monkeypatch.setattr(storage, "upload_audio", lambda _f, owner, _key: (
        f"audio/{owner}/{filename}.webm", 100, "test-sha256",
    ))
    session_id = _start_at_questions(client, "L1-05", 3)
    upload = client.post(f"/v2/lessons/sessions/{session_id}/recording",
        files={"file": ("reading.webm", b"synthetic-data", "audio/webm")},
        headers={"Idempotency-Key": str(uuid4())})
    assert upload.status_code == 200, upload.text
    saved = client.post(f"/v2/lessons/sessions/{session_id}/answers", json={
        "submit_key": str(uuid4()), **upload.json(), "audio_duration_seconds": 3,
    })
    assert saved.status_code == 200, saved.text
    with TestingSessionLocal() as db:
        row = db.query(LessonQuestionResponse).filter(
            LessonQuestionResponse.lesson_session_id == session_id,
        ).one()
        return session_id, row.id, upload.json()["audio_storage_key"]


def queued(client, rid):
    result = client.get("/v2/review/lesson-queue")
    assert result.status_code == 200, result.text
    return next(item for item in result.json()["items"] if item["response_id"] == rid)


def listened(client, rid, item):
    result = client.post(f"/v2/review/lessons/{rid}/audio-completed", json={
        "audio_submission_id": item["audio_submission_id"],
    })
    assert result.status_code == 200, result.text


def retry_upload(client, monkeypatch, task_id):
    import storage
    monkeypatch.setattr(storage, "upload_audio", lambda _f, owner, _key: (
        f"audio/{owner}/replacement.webm", 150, "test-sha256",
    ))
    response = client.post(f"/v2/retries/student/tasks/{task_id}/recording",
        files={"file": ("new.webm", b"synthetic-data", "audio/webm")},
        data={"duration_seconds": "4"},
        headers={"Idempotency-Key": str(uuid4())})
    assert response.status_code == 200, response.text
    return response.json()


def test_lesson_reading_review_is_private_requires_playback_and_updates_evidence(student_client, monkeypatch):
    session_id, rid, _ = reading(student_client, monkeypatch)
    assert student_client.get("/v2/review/lesson-queue").status_code in (401, 403)
    login_staff(student_client)
    item = queued(student_client, rid)
    assert item["interaction"] == "read_aloud" and item["evidence_ready"]
    # Lesson review must expose the original spoken stimulus to the supervisor.
    # It cannot silently fall back to a newer authoring release's text.
    from v2_content.repository import get_pinned_release
    with TestingSessionLocal() as db:
        session = db.get(LessonSession, session_id)
        pinned = get_pinned_release(db, session.content_release_id)
        original = next(q for q in pinned["questions"] if q["id"] == item["question_id"])
        assert item["stimulus_text"] == original["stimulus"]["text"]
    assert item["rubric"] is not None and "text_response" not in item
    body = {"is_correct": True}
    assert student_client.post(f"/v2/review/lessons/{rid}/decision", json=body).status_code == 409
    listened(student_client, rid, item)
    accepted = student_client.post(f"/v2/review/lessons/{rid}/decision", json=body)
    assert accepted.status_code == 200, accepted.text
    assert student_client.post(f"/v2/review/lessons/{rid}/decision", json=body).status_code == 409
    with TestingSessionLocal() as db:
        response = db.get(LessonQuestionResponse, rid)
        proof = db.query(SkillEvidence).filter(SkillEvidence.response_id == rid).one()
        actions = db.query(V2LessonReviewAction).filter(V2LessonReviewAction.lesson_response_id == rid).all()
        assert response.status == "graded" and response.is_correct is True
        assert proof.review_status == "graded" and proof.is_correct is True
        assert proof.counts_for_mastery is False and len(actions) == 1
        assert actions[0].note == ""
    login_student(student_client)
    assert "rubric" not in student_client.get(f"/v2/lessons/sessions/{session_id}/interaction").text


def test_waiting_audio_review_uses_pinned_bank_when_authoring_changes(student_client, monkeypatch):
    """A learner already reviewing audio must not be blocked by a later bank."""
    from v2_content.repository import get_pinned_release, get_release
    import v2_lesson_review as review_module

    session_id, response_id, _ = reading(student_client, monkeypatch)
    with TestingSessionLocal() as db:
        session = db.get(LessonSession, session_id)
        original_checksum = get_pinned_release(db, session.content_release_id)["checksum"]
        session.stage = "waiting_review"
        session.status = "waiting_review"
        db.add(AdaptationDecision(
            lesson_session_id=session.id,
            student_id=session.student_id,
            content_release_id=session.content_release_id,
            decision_key="independent:pending-original-voice",
            decision_kind="waiting_review",
            reason_code="reading_under_human_review",
            evidence_ids=[response_id],
            explanation_json={},
            policy_version="himma-v2-regression/1",
        ))
        db.commit()

    next_release = dict(get_release(), checksum="f" * 64, version="future-release")
    monkeypatch.setattr(review_module, "get_release", lambda: next_release, raising=False)
    resumed = []

    def finish_from_original(db, session, *, decision_key):
        assert get_pinned_release(db, session.content_release_id)["checksum"] == original_checksum
        resumed.append(decision_key)

    monkeypatch.setattr(review_module, "finish_independent_check", finish_from_original)
    login_staff(student_client)
    listened(student_client, response_id, queued(student_client, response_id))
    response = student_client.post(
        f"/v2/review/lessons/{response_id}/decision", json={"is_correct": True},
    )
    assert response.status_code == 200, response.text
    assert resumed == [f"independent:reviewed:{response_id}"]
    with TestingSessionLocal() as db:
        assert db.get(LessonQuestionResponse, response_id).status == "graded"


def test_audio_review_refuses_tampered_private_bank_and_preserves_pending(student_client, monkeypatch):
    session_id, response_id, _ = reading(student_client, monkeypatch)
    login_staff(student_client)
    listened(student_client, response_id, queued(student_client, response_id))
    with TestingSessionLocal() as db:
        session = db.get(LessonSession, session_id)
        original = db.query(PrivateContentBankSnapshot).filter_by(
            content_release_id=session.content_release_id
        ).one()
        original.checksum = "0" * 64
        db.commit()

    response = student_client.post(
        f"/v2/review/lessons/{response_id}/decision", json={"is_correct": True},
    )
    assert response.status_code == 409, response.text
    with TestingSessionLocal() as db:
        row = db.get(LessonQuestionResponse, response_id)
        assert row.status == "pending_review" and row.is_correct is None


def test_missing_private_audio_cannot_be_approved(student_client, monkeypatch):
    import storage
    _, rid, _ = reading(student_client, monkeypatch)
    login_staff(student_client)
    listened(student_client, rid, queued(student_client, rid))
    monkeypatch.setattr(storage, "verify_audio", lambda *a, **kw: (_ for _ in ()).throw(ValueError("missing")))
    denied = student_client.post(f"/v2/review/lessons/{rid}/decision", json={
        "is_correct": True, "note": "ملف الصوت المفقود لا يسمح باعتماد الإجابة",
    })
    assert denied.status_code == 409


def test_rerecord_and_grading_preserve_original_and_idempotency(student_client, monkeypatch):
    _, rid, original = reading(student_client, monkeypatch)
    login_staff(student_client)
    asked = student_client.post(f"/v2/retries/admin/lesson/{rid}/request", json={
        "reason": "التسجيل الأول غير واضح؛ نحتاج إعادة القراءة بصوت مسموع",
    })
    assert asked.status_code == 200, asked.text
    assert asked.json()["request_kind"] == "rerecord"
    task_id = asked.json()["task_id"]
    assert student_client.post(f"/v2/retries/admin/lesson/{rid}/request", json={
        "reason": "إعادة الطلب قبل رد الطالب غير مسموحة",
    }).status_code == 409
    assert queued(student_client, rid)["evidence_ready"] is False
    login_student(student_client)
    task_list = student_client.get("/v2/retries/student/tasks?limit=1").json()
    assert task_list["items"][0]["task_id"] == task_id
    assert "draft_text" not in task_list["items"][0]
    replacement = retry_upload(student_client, monkeypatch, task_id)
    body = {"submit_key": str(uuid4()), **replacement}
    sent = student_client.post(f"/v2/retries/student/tasks/{task_id}/submit", json=body)
    assert sent.status_code == 200, sent.text
    replay = student_client.post(f"/v2/retries/student/tasks/{task_id}/submit", json=body)
    assert replay.status_code == 200 and replay.json()["status"] == "replayed"
    with TestingSessionLocal() as db:
        row = db.get(LessonQuestionResponse, rid)
        task = db.get(V2ReviewRetryTask, task_id)
        assert row.answer_json["answer"]["audio_storage_key"] == original
        assert task.replacement_json["audio_storage_key"] == replacement["audio_storage_key"]
    login_staff(student_client)
    item = queued(student_client, rid)
    assert item["retry_state"] == "submitted"
    listened(student_client, rid, item)
    assert student_client.post(f"/v2/review/lessons/{rid}/decision", json={
        "is_correct": True, "note": "المشرف استمع إلى النسخة الجديدة واعتمد صحة القراءة",
    }).status_code == 200
    with TestingSessionLocal() as db:
        assert db.get(V2ReviewRetryTask, task_id).status == "resolved"


def test_student_cannot_request_staff_review_or_other_student_retry(student_client, monkeypatch):
    _, rid, _ = reading(student_client, monkeypatch)
    assert student_client.post(f"/v2/retries/admin/lesson/{rid}/request", json={
        "reason": "الطالب لا يصدر طلب إعادة للمشرف",
    }).status_code in (401, 403)
    with TestingSessionLocal() as db:
        db.add(Student(access_code="STU002", name="طالب مستقل", current_level=1))
        db.commit()
    login_staff(student_client)
    asked = student_client.post(f"/v2/retries/admin/lesson/{rid}/request", json={
        "reason": "الطالب الأول يحتاج إعادة القراءة بصوت واضح",
    })
    assert asked.status_code == 200, asked.text
    task_id = asked.json()["task_id"]
    login_student(student_client, "STU002")
    assert student_client.get("/v2/retries/student/tasks").json()["items"] == []
    assert student_client.post(f"/v2/retries/student/tasks/{task_id}/submit", json={
        "submit_key": str(uuid4()), "audio_storage_key": "audio/999/foreign.webm",
        "audio_file_size": 100, "audio_mime_type": "audio/webm", "audio_duration_seconds": 3,
    }).status_code == 404
    assert student_client.get("/v2/review/lesson-queue").status_code in (401, 403)


def test_completed_guided_lesson_allows_rerecord_without_resetting_progress(student_client, monkeypatch):
    sid, rid, _ = reading(student_client, monkeypatch)
    with TestingSessionLocal() as db:
        lesson = db.get(LessonSession, sid)
        lesson.status = "completed"
        lesson.stage = "complete"
        lesson.completed_at = datetime.now(timezone.utc)
        db.commit()
    login_staff(student_client)
    asked = student_client.post(f"/v2/retries/admin/lesson/{rid}/request", json={
        "reason": "نحتاج إعادة قراءة واضحة للتمرين الموجه المنجز",
    })
    assert asked.status_code == 200, asked.text
    login_student(student_client)
    audio = retry_upload(student_client, monkeypatch, asked.json()["task_id"])
    assert student_client.post(f"/v2/retries/student/tasks/{asked.json()['task_id']}/submit",
        json={"submit_key": str(uuid4()), **audio}).status_code == 200
    login_staff(student_client)
    listened(student_client, rid, queued(student_client, rid))
    assert student_client.post(f"/v2/review/lessons/{rid}/decision", json={
        "is_correct": True, "note": "القراءة المعادة صحيحة وتم الاستماع للتسجيل",
    }).status_code == 200
    with TestingSessionLocal() as db:
        lesson = db.get(LessonSession, sid)
        assert lesson.status == "completed" and lesson.stage == "complete"
        proof = db.query(SkillEvidence).filter(SkillEvidence.response_id == rid).one()
        assert proof.counts_for_mastery is False


def test_v2_disallows_writing_answers_and_all_three_old_draft_routes(student_client, monkeypatch):
    from v2_interaction_runtime import AnswerRequest
    from v2_content.contracts import AuthoringQuestion
    from v2_content.repository import get_release

    sid, rid, _ = reading(student_client, monkeypatch)
    with pytest.raises(ValidationError):
        AnswerRequest.model_validate({"submit_key": str(uuid4()), "text_response": "باب"})
    question = next(q for q in get_release()["questions"] if q["interaction"] == "read_aloud")
    with pytest.raises(ValidationError):
        AuthoringQuestion.model_validate({**question, "interaction": "write_text"})
    assert student_client.put(f"/v2/lessons/sessions/{sid}/draft", json={"text": "باب"}).status_code == 404
    assert student_client.put("/v2/assessments/sessions/1/draft", json={"text": "باب"}).status_code == 404
    assert student_client.post(f"/v2/retries/student/tasks/{rid}/draft", json={
        "text_response": "باب",
    }).status_code == 404
