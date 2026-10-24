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
    resent = student_client.post(f"/v2/retries/student/tasks/{task_id}/submit", json={
        "submit_key": str(uuid4()), "audio_storage_key": new_key,
        "audio_file_size": 256, "audio_mime_type": "audio/webm", "audio_duration_seconds": 4,
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
