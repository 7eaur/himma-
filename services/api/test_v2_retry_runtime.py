"""P08 complete retry flow for V2 lesson audio and V2 pretest writing."""
from uuid import uuid4

from conftest import TestingSessionLocal
from db.learning_models import AssessmentQuestionResponse, LessonQuestionResponse, StudentJourney, V2ReviewRetryTask
from db.models import AssessmentSession, AudioSubmission, Student
from test_v2_interaction_runtime import _start_at_questions
from v2_content.importer import register_candidate_release
from v2_content.repository import get_release


def _researcher(client):
    assert client.post("/auth/login", json={
        "username": "researcher1", "password": "test-only-researcher-password",
    }).status_code == 200


def _student(client):
    assert client.post("/auth/student-login", json={"access_code": "STU001"}).status_code == 200


def test_p08_pretest_rewrite_resumes_original_30_questions_and_keeps_history(student_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        db.add(StudentJourney(student_id=student.id, content_release_id=release.id, placement_state="in_progress"))
        session = AssessmentSession(
            student_id=student.id, content_release_id=release.id, session_type="pretest",
            status="in_progress", v2_state="waiting_review", v2_question_index=30,
            assessment_attempt_no=1, v2_policy_version="test",
        )
        db.add(session); db.flush()
        target = None
        for question in (q for q in get_release()["questions"] if q["role"] == "pretest"):
            writing = question["id"] == "V2-PRE-Q12"
            row = AssessmentQuestionResponse(
                assessment_session_id=session.id, question_id=question["id"],
                role="pretest", answer_json={"text_response": "النسخة القديمة"} if writing else {"test": True},
                submit_key=str(uuid4()), status="pending_review" if writing else "graded",
                is_correct=None if writing else True,
                skill_group=question["skill_group"], evidence_type=question["evidence_type"],
            )
            db.add(row); db.flush()
            if writing:
                target = row.id
        session_id = session.id
        db.commit()
    assert target is not None
    _researcher(student_client)
    request = student_client.post(f"/v2/retries/admin/assessment/{target}/request", json={
        "reason": "النص السابق غير كاف للتحكيم؛ يرجى إعادة كتابة الإجابة بوضوح",
    })
    assert request.status_code == 200, request.text
    task_id = request.json()["task_id"]
    queue = student_client.get("/v2/assessments/admin/review-queue").json()["items"]
    pending = next(item for item in queue if item["response_id"] == target)
    assert pending["retry_state"] == "requested" and pending["evidence_ready"] is False
    assert student_client.post(f"/v2/assessments/admin/responses/{target}/review", json={
        "is_correct": True, "note": "غير جائز قبل إعادة الكتابة",
    }).status_code == 409
    _student(student_client)
    student_tasks = student_client.get("/v2/retries/student/tasks").json()["items"]
    assert any(task["task_id"] == task_id and task["question_id"] == "V2-PRE-Q12" for task in student_tasks)
    result = student_client.post(f"/v2/retries/student/tasks/{task_id}/submit", json={
        "submit_key": str(uuid4()), "text_response": "باب",
    })
    assert result.status_code == 200, result.text
    _researcher(student_client)
    latest = next(item for item in student_client.get("/v2/assessments/admin/review-queue").json()["items"]
                  if item["response_id"] == target)
    assert latest["retry_state"] == "submitted"
    assert latest["text_response"] == "باب" and latest["evidence_ready"] is True
    grade = student_client.post(f"/v2/assessments/admin/responses/{target}/review", json={
        "is_correct": True, "note": "تحققت من تطابق الكلمة مع مرجع السؤال",
    })
    assert grade.status_code == 200, grade.text
    with TestingSessionLocal() as db:
        original = db.query(AssessmentQuestionResponse).filter(AssessmentQuestionResponse.id == target).one()
        task = db.query(V2ReviewRetryTask).filter(V2ReviewRetryTask.id == task_id).one()
        session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).one()
        assert original.answer_json["text_response"] == "النسخة القديمة"
        assert task.replacement_json["text_response"] == "باب" and task.status == "resolved"
        assert original.status == "graded"
        assert session.v2_state == "placement_pending_review"


def test_p08_learner_audio_retry_never_overwrites_original_recording(student_client, monkeypatch):
    import storage
    monkeypatch.setattr(storage, "verify_audio", lambda *a, **kw: None)
    sid = _start_at_questions(student_client, "L1-05", 3)
    with TestingSessionLocal() as db:
        student_id = db.query(Student).filter(Student.access_code == "STU001").one().id
    original_key = f"audio/{student_id}/original.webm"
    sent = student_client.post(f"/v2/lessons/sessions/{sid}/answers", json={
        "submit_key": str(uuid4()), "audio_storage_key": original_key,
        "audio_file_size": 132, "audio_mime_type": "audio/webm", "audio_duration_seconds": 3,
    })
    assert sent.status_code == 200, sent.text
    with TestingSessionLocal() as db:
        original = db.query(LessonQuestionResponse).filter(LessonQuestionResponse.lesson_session_id == sid).one()
        response_id = original.id
    _researcher(student_client)
    request = student_client.post(f"/v2/retries/admin/lesson/{response_id}/request", json={
        "reason": "التسجيل الأول غير واضح؛ يُرجى القراءة مرة أخرى بصوت مسموع",
    })
    assert request.status_code == 200, request.text
    task_id = request.json()["task_id"]
    _student(student_client)
    new_key = f"audio/{student_id}/updated.webm"
    # A rerecord request cannot accept a previously uploaded audio key unless
    # the new recording was staged for this specific task.
    rejected_old = student_client.post(f"/v2/retries/student/tasks/{task_id}/submit", json={
        "submit_key": str(uuid4()), "audio_storage_key": original_key,
        "audio_file_size": 132, "audio_mime_type": "audio/webm", "audio_duration_seconds": 3,
    })
    assert rejected_old.status_code == 409
    monkeypatch.setattr(storage, "upload_audio",
                        lambda _file, owner, _op: (new_key, 256, "test-sha256"))
    staged = student_client.post(
        f"/v2/retries/student/tasks/{task_id}/recording",
        files={"file": ("rerecorded.webm", b"test-fixture-only", "audio/webm")},
        data={"duration_seconds": "4"},
        headers={"Idempotency-Key": "unique-retry-key-1"},
    )
    assert staged.status_code == 200, staged.text
    resent = student_client.post(f"/v2/retries/student/tasks/{task_id}/submit", json={
        "submit_key": str(uuid4()), **staged.json(),
    })
    assert resent.status_code == 200, resent.text
    _researcher(student_client)
    queue = student_client.get("/v2/review/lesson-queue").json()["items"]
    item = next(x for x in queue if x["response_id"] == response_id)
    assert item["retry_state"] == "submitted" and item["evidence_ready"] is True
    grade = student_client.post(f"/v2/review/lessons/{response_id}/decision", json={
        "is_correct": True, "note": "تم الاستماع للنسخة الجديدة وتقييمها",
    })
    assert grade.status_code == 200, grade.text
    with TestingSessionLocal() as db:
        all_audio = db.query(AudioSubmission).filter(
            AudioSubmission.lesson_response_id == response_id,
        ).order_by(AudioSubmission.id).all()
        task = db.query(V2ReviewRetryTask).filter(V2ReviewRetryTask.id == task_id).one()
        assert len(all_audio) == 2
        assert all_audio[0].storage_key == original_key and all_audio[0].status == "rerecord_required"
        assert all_audio[1].storage_key == new_key and all_audio[1].status == "graded"
        assert task.audio_submission_id == all_audio[1].id and task.status == "resolved"


def test_p08_rerecord_stage_survives_reload_and_rejects_wrong_file(student_client, monkeypatch):
    """S3 upload acknowledgement can be lost; the next authenticated GET recovers it."""
    import storage

    monkeypatch.setattr(storage, "verify_audio", lambda *args, **kwargs: None)
    sid = _start_at_questions(student_client, "L1-05", 3)
    with TestingSessionLocal() as db:
        student_id = db.query(Student).filter(Student.access_code == "STU001").one().id
    sent = student_client.post(f"/v2/lessons/sessions/{sid}/answers", json={
        "submit_key": str(uuid4()), "audio_storage_key": f"audio/{student_id}/original.webm",
        "audio_file_size": 110, "audio_mime_type": "audio/webm", "audio_duration_seconds": 3,
    })
    assert sent.status_code == 200, sent.text
    with TestingSessionLocal() as db:
        original = db.query(LessonQuestionResponse).filter(LessonQuestionResponse.lesson_session_id == sid).one()
        response_id = original.id
    _researcher(student_client)
    asked = student_client.post(f"/v2/retries/admin/lesson/{response_id}/request", json={
        "reason": "الصوت السابق غير مسموع جيدًا؛ يُرجى إعادة قراءة الكلمة بوضوح",
    })
    assert asked.status_code == 200, asked.text
    task_id = asked.json()["task_id"]
    _student(student_client)
    def fake_upload(file, owner, operation):
        return f"audio/{owner}/staged-{operation.rsplit(':', 1)[-1]}.webm", 128, "digest"
    monkeypatch.setattr(storage, "upload_audio", fake_upload)
    route = f"/v2/retries/student/tasks/{task_id}/recording"
    form = {"file": ("reading.webm", b"test-fixture-only-binary", "audio/webm;codecs=opus")}
    upload = student_client.post(route, files=form, data={"duration_seconds": "4"},
                                 headers={"Idempotency-Key": "stage-test-key-1"})
    assert upload.status_code == 200, upload.text
    meta = upload.json()
    assert meta["audio_duration_seconds"] == 4
    again = student_client.post(route, files=form, data={"duration_seconds": "4"},
                                headers={"Idempotency-Key": "stage-test-key-1"})
    assert again.status_code == 200 and again.json() == meta
    tasks = student_client.get("/v2/retries/student/tasks")
    assert tasks.status_code == 200
    task = next(x for x in tasks.json()["items"] if x["task_id"] == task_id)
    assert task["staged_audio"] == meta
    # Student may intentionally rerecord; retain the old private object key.
    replaced = student_client.post(route, files=form, data={"duration_seconds": "5"},
                                   headers={"Idempotency-Key": "stage-test-key-2"})
    assert replaced.status_code == 200, replaced.text
    new_meta = replaced.json()
    task_now = next(x for x in student_client.get("/v2/retries/student/tasks").json()["items"]
                    if x["task_id"] == task_id)
    assert task_now["staged_audio"] == new_meta
    meta = new_meta
    bad = student_client.post(f"/v2/retries/student/tasks/{task_id}/submit",
                              json={"submit_key": str(uuid4()), "audio_storage_key": f"audio/{student_id}/wrong.webm",
                                    "audio_file_size": 128, "audio_mime_type": "audio/webm;codecs=opus",
                                    "audio_duration_seconds": 4})
    assert bad.status_code == 409
    accepted = student_client.post(f"/v2/retries/student/tasks/{task_id}/submit",
                                   json={"submit_key": str(uuid4()), **meta})
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["awaiting_human_review"]
    with TestingSessionLocal() as db:
        task = db.query(V2ReviewRetryTask).filter(V2ReviewRetryTask.id == task_id).one()
        assert task.status == "submitted"
        assert task.audio_submission_id is not None
        assert task.replacement_json["audio_storage_key"] == meta["audio_storage_key"]
        assert len(task.replacement_json["superseded_staged_audio"]) == 1
        assert task.replacement_json["superseded_staged_audio"][0]["audio_storage_key"] != meta["audio_storage_key"]


def test_p08_invalid_audio_type_rejected_before_upload(student_client, monkeypatch):
    import storage
    sid = _start_at_questions(student_client, "L1-05", 3)
    with TestingSessionLocal() as db:
        student_id = db.query(Student).filter(Student.access_code == "STU001").one().id
    monkeypatch.setattr(storage, "verify_audio", lambda *args, **kwargs: None)
    assert student_client.post(f"/v2/lessons/sessions/{sid}/answers", json={
        "submit_key": str(uuid4()), "audio_storage_key": f"audio/{student_id}/initial.webm",
        "audio_file_size": 120, "audio_mime_type": "audio/webm", "audio_duration_seconds": 3,
    }).status_code == 200
    with TestingSessionLocal() as db:
        rid = db.query(LessonQuestionResponse).filter(LessonQuestionResponse.lesson_session_id == sid).one().id
    _researcher(student_client)
    task_id = student_client.post(f"/v2/retries/admin/lesson/{rid}/request", json={
        "reason": "أعد قراءة الصوت السابق لأنه غير واضح",
    }).json()["task_id"]
    _student(student_client)
    def unexpected_upload(*args, **kwargs):
        raise AssertionError("S3 must not receive an invalid audio MIME")
    monkeypatch.setattr(storage, "upload_audio", unexpected_upload)
    blocked = student_client.post(f"/v2/retries/student/tasks/{task_id}/recording",
        files={"file": ("bad.pdf", b"fake", "application/pdf")},
        data={"duration_seconds": "4"}, headers={"Idempotency-Key": "stage-invalid-type"})
    assert blocked.status_code == 400
