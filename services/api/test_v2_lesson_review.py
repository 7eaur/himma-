"""P08 lesson review contract: authorization, immutable decisions, no fake grade."""
from uuid import uuid4
from unittest.mock import patch

from conftest import TestingSessionLocal
from db.learning_models import LessonQuestionResponse, SkillEvidence, V2LessonReviewAction, LessonSession, StudentJourney
from db.models import Student
from test_v2_interaction_runtime import _start_at_questions
from test_v2_legacy_writing_fixture import legacy_writing_release
from v2_content.repository import get_question
from v2_content.importer import register_candidate_release


def _writing_response(student_client):
    """Frozen old-format writing evidence for regression, absent from current bank."""
    sid = _start_at_questions(student_client, "L2-01", 3)
    release = legacy_writing_release("L2-01-GP-04", "L2-01-IC-A02")
    with TestingSessionLocal() as db:
        historical = register_candidate_release(db, release)
        session = db.query(LessonSession).filter(LessonSession.id == sid).one()
        session.content_release_id = historical.id
        journey = db.query(StudentJourney).filter(StudentJourney.student_id == session.student_id).one()
        journey.content_release_id = historical.id
        db.commit()
    question_id = "L2-01-GP-04"
    old_question = next(q for q in release["questions"] if q["id"] == question_id)
    with patch("v2_interaction_runtime.get_question",
               side_effect=lambda key: old_question if key == question_id else get_question(key)):
        submitted = student_client.post(
            f"/v2/lessons/sessions/{sid}/answers",
            json={"submit_key": str(uuid4()), "text_response": "القلم"},
        )
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["submission"]["status"] == "pending_review"
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
    # The student's retry inbox has explicit pagination, not an invisible 50-task cut.
    first_page = student_client.get("/v2/retries/student/tasks?limit=1&offset=0")
    last_page = student_client.get("/v2/retries/student/tasks?limit=1&offset=1")
    assert first_page.status_code == 200 and last_page.status_code == 200
    assert first_page.json()["items"][0]["task_id"] == task_id
    assert first_page.json()["next_offset"] is None
    assert last_page.json() == {"items": [], "next_offset": None}
    assert student_client.get("/v2/retries/student/tasks?offset=-1").status_code == 422
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


def test_p08_completed_guided_lesson_still_allows_retry_without_reopening_student_progress(student_client):
    """A guided answer can remain neutral after the lesson journey advances."""
    from db.learning_models import LessonSession, V2ReviewRetryTask
    from datetime import datetime, timezone

    sid, qid = _writing_response(student_client)
    with TestingSessionLocal() as db:
        session = db.query(LessonSession).filter(LessonSession.id == sid).one()
        response = db.query(LessonQuestionResponse).filter(
            LessonQuestionResponse.lesson_session_id == sid,
            LessonQuestionResponse.question_id == qid,
        ).one()
        assert response.role == "guided_practice"
        rid = response.id
        session.stage = "complete"
        session.status = "completed"
        session.completed_at = datetime.now(timezone.utc)
        db.commit()

    _login_researcher(student_client)
    asked = student_client.post(f"/v2/retries/admin/lesson/{rid}/request", json={
        "reason": "وصلت إجابة التمرين الموجه ولكن نحتاج كتابتها مجددًا بوضوح",
    })
    assert asked.status_code == 200, asked.text
    task_id = asked.json()["task_id"]
    assert student_client.post("/auth/student-login", json={"access_code": "STU001"}).status_code == 200
    tasks = student_client.get("/v2/retries/student/tasks")
    assert tasks.status_code == 200
    assert any(t["task_id"] == task_id for t in tasks.json()["items"])
    result = student_client.post(f"/v2/retries/student/tasks/{task_id}/submit", json={
        "submit_key": str(uuid4()), "text_response": "باب",
    })
    assert result.status_code == 200, result.text
    _login_researcher(student_client)
    reviewed = student_client.post(f"/v2/review/lessons/{rid}/decision", json={
        "is_correct": True, "note": "جرى تقييم الكتابة الجديدة بعد اكتمال التمرين الموجه",
    })
    assert reviewed.status_code == 200, reviewed.text
    with TestingSessionLocal() as db:
        session = db.query(LessonSession).filter(LessonSession.id == sid).one()
        evidence = db.query(SkillEvidence).filter(SkillEvidence.response_id == rid).one()
        task = db.query(V2ReviewRetryTask).filter(V2ReviewRetryTask.id == task_id).one()
        assert session.stage == "complete" and session.status == "completed"
        assert evidence.is_correct is True and evidence.counts_for_mastery is False
        assert task.status == "resolved"


def test_p08_students_cannot_read_or_submit_other_student_retry_task(student_client):
    sid, qid = _writing_response(student_client)
    with TestingSessionLocal() as db:
        row = db.query(LessonQuestionResponse).filter(
            LessonQuestionResponse.lesson_session_id == sid,
            LessonQuestionResponse.question_id == qid,
        ).one()
        rid = row.id
        db.add(Student(access_code="STU002", name="طالب مستقل", current_level=1))
        db.commit()
    _login_researcher(student_client)
    asked = student_client.post(f"/v2/retries/admin/lesson/{rid}/request", json={
        "reason": "أعد كتابة الكلمة لأتمكن من مراجعتها بوضوح",
    })
    assert asked.status_code == 200, asked.text
    task_id = asked.json()["task_id"]
    assert student_client.post("/auth/student-login", json={"access_code": "STU002"}).status_code == 200
    tasks = student_client.get("/v2/retries/student/tasks")
    assert tasks.status_code == 200 and tasks.json()["items"] == []
    result = student_client.post(f"/v2/retries/student/tasks/{task_id}/submit", json={
        "submit_key": str(uuid4()), "text_response": "باب",
    })
    assert result.status_code == 404
    draft = student_client.post(f"/v2/retries/student/tasks/{task_id}/draft",
                                json={"text_response": "لا يمكنني حفظ مسودة طالب آخر"})
    assert draft.status_code == 404
    assert student_client.get("/v2/review/lesson-queue").status_code in (401, 403)
    assert student_client.post(f"/v2/review-claims/admin/lesson/{rid}/claim").status_code in (401, 403)


def test_p08_student_retry_inbox_paginates_two_distinct_pending_answers(student_client):
    from db.learning_models import LessonSession, V2ReviewRetryTask
    from db.models import User

    sid, first_question_id = _writing_response(student_client)
    with TestingSessionLocal() as db:
        session = db.query(LessonSession).filter(LessonSession.id == sid).one()
        first = db.query(LessonQuestionResponse).filter(
            LessonQuestionResponse.lesson_session_id == sid,
            LessonQuestionResponse.question_id == first_question_id,
        ).one()
        reviewer_id = db.query(User).filter(User.username == "researcher1").one().id
        second = LessonQuestionResponse(
            lesson_session_id=sid, question_id="L2-01-IC-A02",
            role="independent_check",
            answer_json={"answer": {"text_response": "محاولة كتابة ثانية"}},
            submit_key=str(uuid4()), status="pending_review",
        )
        db.add(second)
        db.flush()
        db.add_all([
            V2ReviewRetryTask(
                lesson_response_id=first.id, student_id=session.student_id,
                requested_by=reviewer_id, request_kind="rewrite", status="requested",
                reason="اطلب إعادة كتابة التدريب الموجه",
            ),
            V2ReviewRetryTask(
                lesson_response_id=second.id, student_id=session.student_id,
                requested_by=reviewer_id, request_kind="rewrite", status="requested",
                reason="اطلب إعادة كتابة التحقق المستقل",
            ),
        ])
        db.commit()

    page1 = student_client.get("/v2/retries/student/tasks?limit=1&offset=0")
    page2 = student_client.get("/v2/retries/student/tasks?limit=1&offset=1")
    page3 = student_client.get("/v2/retries/student/tasks?limit=1&offset=2")
    assert (page1.status_code, page2.status_code, page3.status_code) == (200, 200, 200)
    assert page1.json()["next_offset"] == 1
    assert page2.json()["next_offset"] is None
    assert page3.json() == {"items": [], "next_offset": None}
    assert {page1.json()["items"][0]["question_id"], page2.json()["items"][0]["question_id"]} == {
        first_question_id, "L2-01-IC-A02",
    }


def test_p08_rewrite_draft_recovers_after_reload_without_grading(student_client):
    from db.learning_models import V2ReviewRetryTask

    sid, qid = _writing_response(student_client)
    with TestingSessionLocal() as db:
        rid = db.query(LessonQuestionResponse).filter(
            LessonQuestionResponse.lesson_session_id == sid,
            LessonQuestionResponse.question_id == qid,
        ).one().id

    _login_researcher(student_client)
    request = student_client.post(f"/v2/retries/admin/lesson/{rid}/request", json={
        "reason": "الكتابة السابقة لم تكن واضحة؛ أعد كتابة الإجابة قبل المراجعة",
    })
    assert request.status_code == 200, request.text
    task_id = request.json()["task_id"]

    assert student_client.post("/auth/student-login", json={"access_code": "STU001"}).status_code == 200
    draft = student_client.post(f"/v2/retries/student/tasks/{task_id}/draft",
                                json={"text_response": "مسودة لا تدخل التقييم"})
    assert draft.status_code == 200, draft.text
    assert draft.json()["status"] == "draft_saved"
    inbox = student_client.get("/v2/retries/student/tasks")
    assert inbox.status_code == 200, inbox.text
    saved = next(x for x in inbox.json()["items"] if x["task_id"] == task_id)
    assert saved["draft_text"] == "مسودة لا تدخل التقييم"
    assert saved["status"] == "requested"

    with TestingSessionLocal() as db:
        answer = db.query(LessonQuestionResponse).filter(LessonQuestionResponse.id == rid).one()
        task = db.query(V2ReviewRetryTask).filter(V2ReviewRetryTask.id == task_id).one()
        assert answer.status == "pending_review" and answer.is_correct is None
        assert task.status == "requested" and task.replacement_json == {"draft_text": "مسودة لا تدخل التقييم"}

    saved_again = student_client.post(f"/v2/retries/student/tasks/{task_id}/draft",
                                      json={"text_response": "باب"})
    assert saved_again.status_code == 200
    sent = student_client.post(f"/v2/retries/student/tasks/{task_id}/submit",
                               json={"submit_key": str(uuid4()), "text_response": "باب"})
    assert sent.status_code == 200, sent.text
    assert student_client.post(f"/v2/retries/student/tasks/{task_id}/draft",
                               json={"text_response": "لا تغير جوابًا مرسلًا"}).status_code == 409
    with TestingSessionLocal() as db:
        task = db.query(V2ReviewRetryTask).filter(V2ReviewRetryTask.id == task_id).one()
        assert task.status == "submitted" and task.replacement_json["text_response"] == "باب"


def test_p08_audio_retry_cannot_save_a_writing_draft(student_client, monkeypatch):
    import storage
    from db.learning_models import LessonQuestionResponse

    monkeypatch.setattr(storage, "verify_audio", lambda *args, **kwargs: None)
    sid = _start_at_questions(student_client, "L1-05", 3)
    with TestingSessionLocal() as db:
        student_id = db.query(Student).filter(Student.access_code == "STU001").one().id
    response = student_client.post(f"/v2/lessons/sessions/{sid}/answers", json={
        "submit_key": str(uuid4()), "audio_storage_key": f"audio/{student_id}/first.webm",
        "audio_file_size": 100, "audio_mime_type": "audio/webm",
        "audio_duration_seconds": 3,
    })
    assert response.status_code == 200, response.text
    with TestingSessionLocal() as db:
        rid = db.query(LessonQuestionResponse).filter(
            LessonQuestionResponse.lesson_session_id == sid
        ).one().id
    _login_researcher(student_client)
    asked = student_client.post(f"/v2/retries/admin/lesson/{rid}/request", json={
        "reason": "التسجيل غير واضح؛ حاول القراءة مرة أخرى بوضوح",
    })
    assert asked.status_code == 200, asked.text
    task_id = asked.json()["task_id"]
    assert student_client.post("/auth/student-login", json={"access_code": "STU001"}).status_code == 200
    assert student_client.post(f"/v2/retries/student/tasks/{task_id}/draft",
                               json={"text_response": "نص لا ينطبق على التسجيل"}).status_code == 409
