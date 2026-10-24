"""P08 lesson review contract: authorization, immutable decisions, no fake grade."""
from uuid import uuid4

from conftest import TestingSessionLocal
from db.learning_models import LessonQuestionResponse, SkillEvidence, V2LessonReviewAction
from db.models import Student
from test_v2_interaction_runtime import _start_at_questions


def _writing_response(student_client):
    sid = _start_at_questions(student_client, "L2-01", 3)
    question_id = student_client.get(f"/v2/lessons/sessions/{sid}/interaction").json()["interaction"]["question"]["question_id"]
    sent = student_client.post(
        f"/v2/lessons/sessions/{sid}/answers",
        json={"submit_key": str(uuid4()), "text_response": "القلم"},
    )
    assert sent.status_code == 200, sent.text
    assert sent.json()["submission"]["status"] == "pending_review"
    return sid, question_id


def _login_researcher(client):
    response = client.post("/auth/login", json={
        "username": "researcher1", "password": "test-only-researcher-password",
    })
    assert response.status_code == 200


def test_p08_lesson_queue_is_private_and_grade_updates_skill_evidence(student_client):
    sid, qid = _writing_response(student_client)
    assert student_client.get("/v2/review/lesson-queue").status_code in (401, 403)
    _login_researcher(student_client)
    researcher_client = student_client
    queue = researcher_client.get("/v2/review/lesson-queue?limit=25")
    assert queue.status_code == 200, queue.text
    item = next(row for row in queue.json()["items"] if row["session_id"] == sid and row["question_id"] == qid)
    assert item["text_response"] == "القلم"
    assert item["evidence_ready"] is True
    assert item["rubric"] is not None
    res = researcher_client.post(
        f"/v2/review/lessons/{item['response_id']}/decision",
        json={"is_correct": True, "note": "مطابق لمعيار إجابة الكتابة"},
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "graded"
    again = researcher_client.post(
        f"/v2/review/lessons/{item['response_id']}/decision",
        json={"is_correct": False, "note": "قرار آخر"},
    )
    assert again.status_code == 409
    with TestingSessionLocal() as db:
        row = db.query(LessonQuestionResponse).filter(LessonQuestionResponse.id == item["response_id"]).one()
        proof = db.query(SkillEvidence).filter(SkillEvidence.response_id == row.id).one()
        history = db.query(V2LessonReviewAction).filter(V2LessonReviewAction.lesson_response_id == row.id).all()
        assert row.status == "graded" and row.is_correct is True
        assert proof.review_status == "graded" and proof.is_correct is True
        assert proof.counts_for_mastery is False  # guided practice never counts for mastery
        assert len(history) == 1 and history[0].note == "مطابق لمعيار إجابة الكتابة"
    # A learner never receives the private rubric after logging in again.
    assert student_client.post("/auth/student-login", json={"access_code": "STU001"}).status_code == 200
    assert "rubric" not in student_client.get(f"/v2/lessons/sessions/{sid}/interaction").text


def test_p08_lesson_decision_rejects_evidence_without_audio(student_client, monkeypatch):
    import v2_interaction_runtime
    monkeypatch.setattr(v2_interaction_runtime.storage, "verify_audio", lambda *a, **kw: None)
    sid = _start_at_questions(student_client, "L1-05", 3)
    with TestingSessionLocal() as db:
        student_id = db.query(Student).filter(Student.access_code == "STU001").one().id
    sent = student_client.post(
        f"/v2/lessons/sessions/{sid}/answers",
        json={"submit_key": str(uuid4()), "audio_storage_key": f"audio/{student_id}/test-p08.webm",
              "audio_file_size": 100, "audio_mime_type": "audio/webm", "audio_duration_seconds": 3},
    )
    assert sent.status_code == 200, sent.text
    _login_researcher(student_client)
    researcher_client = student_client
    queue = researcher_client.get("/v2/review/lesson-queue").json()["items"]
    item = next(row for row in queue if row["session_id"] == sid)
    # Reviewer cannot mark a recording as read if the private S3 object is not there.
    monkeypatch.setattr(v2_interaction_runtime.storage, "verify_audio", lambda *a, **kw: (_ for _ in ()).throw(ValueError("gone")))
    graded = researcher_client.post(f"/v2/review/lessons/{item['response_id']}/decision",
                                     json={"is_correct": True, "note": "حاول اعتماد التسجيل"})
    assert graded.status_code == 409


def test_p08_rewrite_request_resubmit_and_human_decision_preserve_original(student_client):
    from db.learning_models import V2ReviewRetryTask
    sid, qid = _writing_response(student_client)
    _login_researcher(student_client)
    queue = student_client.get("/v2/review/lesson-queue").json()["items"]
    item = next(x for x in queue if x["session_id"] == sid and x["question_id"] == qid)
    original_id = item["response_id"]
    asked = student_client.post(
        f"/v2/retries/admin/lesson/{original_id}/request",
        json={"reason": "الكلمة المرسلة لا تطابق صورة السؤال، يرجى كتابتها ثانية"},
    )
    assert asked.status_code == 200, asked.text
    task_id = asked.json()["task_id"]
    twice = student_client.post(
        f"/v2/retries/admin/lesson/{original_id}/request",
        json={"reason": "أعد الإجابة مرة ثانية"},
    )
    assert twice.status_code == 409
    waiting = next(x for x in student_client.get("/v2/review/lesson-queue").json()["items"]
                   if x["response_id"] == original_id)
    assert waiting["retry_state"] == "requested" and waiting["evidence_ready"] is False
    assert student_client.post(
        f"/v2/review/lessons/{original_id}/decision",
        json={"is_correct": True, "note": "لم يصل التصحيح"},
    ).status_code == 409
    # Researcher and student share one test cookie: switch identity explicitly.
    assert student_client.post("/auth/student-login", json={"access_code": "STU001"}).status_code == 200
    tasks = student_client.get("/v2/retries/student/tasks")
    assert tasks.status_code == 200
    assert any(task["task_id"] == task_id for task in tasks.json()["items"])
    submit_key = str(uuid4())
    submitted = student_client.post(f"/v2/retries/student/tasks/{task_id}/submit", json={
        "submit_key": submit_key, "text_response": "باب",
    })
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["awaiting_human_review"]
    replay = student_client.post(f"/v2/retries/student/tasks/{task_id}/submit", json={
        "submit_key": submit_key, "text_response": "باب",
    })
    assert replay.status_code == 200 and replay.json()["status"] == "replayed"
    _login_researcher(student_client)
    new_item = next(x for x in student_client.get("/v2/review/lesson-queue").json()["items"]
                    if x["response_id"] == original_id)
    assert new_item["retry_state"] == "submitted"
    assert new_item["text_response"] == "باب"
    graded = student_client.post(f"/v2/review/lessons/{original_id}/decision", json={
        "is_correct": True, "note": "الإجابة الجديدة صحيحة حسب معيار الكتابة",
    })
    assert graded.status_code == 200, graded.text
    with TestingSessionLocal() as db:
        response = db.query(LessonQuestionResponse).filter(LessonQuestionResponse.id == original_id).one()
        task = db.query(V2ReviewRetryTask).filter(V2ReviewRetryTask.id == task_id).one()
        assert response.answer_json["answer"]["text_response"] == "القلم"
        assert task.status == "resolved" and task.replacement_json["text_response"] == "باب"
        assert response.status == "graded"


def test_p08_students_cannot_request_retry_for_themselves(student_client):
    sid, qid = _writing_response(student_client)
    with TestingSessionLocal() as db:
        response = db.query(LessonQuestionResponse).filter(
            LessonQuestionResponse.lesson_session_id == sid,
            LessonQuestionResponse.question_id == qid,
        ).one()
        response_id = response.id
    assert student_client.post(
        f"/v2/retries/admin/lesson/{response_id}/request",
        json={"reason": "اختبار الصلاحيات يحظر الطالب"},
    ).status_code in (401, 403)
