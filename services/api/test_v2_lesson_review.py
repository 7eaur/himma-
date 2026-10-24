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


def test_p08_lesson_queue_is_private_and_grade_updates_skill_evidence(student_client, researcher_client):
    sid, qid = _writing_response(student_client)
    assert student_client.get("/v2/review/lesson-queue").status_code in (401, 403)
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
    assert "rubric" not in student_client.get(f"/v2/lessons/sessions/{sid}/interaction").text


def test_p08_lesson_decision_rejects_evidence_without_audio(student_client, researcher_client, monkeypatch):
    import v2_interaction_runtime
    monkeypatch.setattr(v2_interaction_runtime.storage, "verify_audio", lambda *a, **kw: None)
    sid = _start_at_questions(student_client, "L1-05", 3)
    sent = student_client.post(
        f"/v2/lessons/sessions/{sid}/answers",
        json={"submit_key": str(uuid4()), "audio_storage_key": "audio/1/test-p08.webm",
              "audio_file_size": 100, "audio_mime_type": "audio/webm", "audio_duration_seconds": 3},
    )
    assert sent.status_code == 200, sent.text
    queue = researcher_client.get("/v2/review/lesson-queue").json()["items"]
    item = next(row for row in queue if row["session_id"] == sid)
    # Reviewer cannot mark a recording as read if the private S3 object is not there.
    monkeypatch.setattr(v2_interaction_runtime.storage, "verify_audio", lambda *a, **kw: (_ for _ in ()).throw(ValueError("gone")))
    graded = researcher_client.post(f"/v2/review/lessons/{item['response_id']}/decision",
                                     json={"is_correct": True, "note": "حاول اعتماد التسجيل"})
    assert graded.status_code == 409
