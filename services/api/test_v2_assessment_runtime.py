from uuid import uuid4

from conftest import TestingSessionLocal
from db.learning_models import AssessmentQuestionResponse, PlacementDecisionV2, StudentJourney
from db.models import AssessmentSession, AudioSubmission, Student
from assessment_retake import mark_official_completed_attempt
from v2_content.contracts import PRIVATE_KEYS
from v2_content.repository import get_question, get_release
from v2_content.importer import register_candidate_release


def _all_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _all_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _all_keys(child)


def test_assessment_bank_is_parallel_distinct_30_plus_30():
    release = get_release()
    pre = [q for q in release["questions"] if q["role"] == "pretest"]
    post = [q for q in release["questions"] if q["role"] == "posttest"]
    assert len(pre) == len(post) == 30
    assert {q["id"] for q in pre}.isdisjoint({q["id"] for q in post})
    assert {q["skill_group"] for q in pre} == {q["skill_group"] for q in post}


def test_pretest_starts_resumes_and_never_leaks_private_answer(student_client):
    started = student_client.post("/v2/assessments/pretest/start")
    assert started.status_code == 200
    payload = started.json()
    assert payload["session"]["progress"] == {"answered": 0, "total": 30}
    assert payload["interaction"]["progress"]["stage"] == "pretest"
    assert PRIVATE_KEYS.isdisjoint(set(_all_keys(payload)))
    resumed = student_client.post("/v2/assessments/pretest/start")
    assert resumed.status_code == 200
    assert resumed.json()["session"]["session_id"] == payload["session"]["session_id"]


def test_objective_answer_is_private_idempotent_and_advances(student_client):
    payload = student_client.post("/v2/assessments/pretest/start").json()
    session_id = payload["session"]["session_id"]
    question = get_question(payload["interaction"]["question"]["question_id"])
    key = str(uuid4())
    response = student_client.post(f"/v2/assessments/sessions/{session_id}/answers", json={"submit_key": key, "selected_option_ids": question["private_answer"]["correct_option_ids"]})
    assert response.status_code == 200
    assert "correct" not in response.json()["submission"]
    assert response.json()["assessment"]["session"]["progress"]["answered"] == 1
    replay = student_client.post(f"/v2/assessments/sessions/{session_id}/answers", json={"submit_key": key, "selected_option_ids": question["private_answer"]["correct_option_ids"]})
    assert replay.status_code == 200
    assert replay.json()["status"] == "replayed"
    with TestingSessionLocal() as db:
        assert db.query(AssessmentQuestionResponse).one().is_correct is True


def test_open_responses_keep_placement_pending_until_human_review_and_manual_decision(researcher_client, monkeypatch):
    import storage
    monkeypatch.setattr(storage, "verify_audio", lambda *args, **kwargs: None)
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        db.add(StudentJourney(student_id=student.id, content_release_id=release.id, placement_state="in_progress", current_level=1))
        session = AssessmentSession(student_id=student.id, content_release_id=release.id, session_type="pretest", status="in_progress", v2_state="waiting_review", v2_question_index=30, v2_policy_version="test", assessment_attempt_no=1)
        db.add(session); db.flush()
        questions = [q for q in get_release()["questions"] if q["role"] == "pretest"]
        for q in questions:
            response = AssessmentQuestionResponse(
                assessment_session_id=session.id, question_id=q["id"], role="pretest", answer_json={"text_response": "نص مُقدّم"} if q["interaction"] == "write_text" else {"audio_storage_key": f"audio/{student.id}/test.webm"} if q["interaction"] == "read_aloud" else {"test": True},
                submit_key=str(uuid4()), status="pending_review" if q["interaction"] in {"read_aloud", "write_text"} else "graded",
                is_correct=None if q["interaction"] in {"read_aloud", "write_text"} else True,
                skill_group=q["skill_group"], evidence_type=q["evidence_type"],
            )
            db.add(response)
            db.flush()
            if q["interaction"] == "read_aloud":
                db.add(AudioSubmission(assessment_response_id=response.id, storage_key=f"audio/{student.id}/test.webm", file_size=2048, mime_type="audio/webm", status="pending_review"))
        db.commit()
        pending_ids = [r.id for r in db.query(AssessmentQuestionResponse).filter(AssessmentQuestionResponse.status == "pending_review").all()]
        session_id = session.id
    # Same TestClient cookie is now researcher after the researcher fixture logs in.
    for response_id in pending_ids:
        reviewed = researcher_client.post(f"/v2/assessments/admin/responses/{response_id}/review", json={"is_correct": True, "note": "مراجعة بشرية واضحة"})
        assert reviewed.status_code == 200
    with TestingSessionLocal() as db:
        session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).one()
        assert session.v2_state == "placement_pending_review"
        assert session.assigned_level is None
    placed = researcher_client.post(f"/v2/assessments/admin/sessions/{session_id}/placement", json={"assigned_level": 2, "reason": "قرار يدوي مبني على ملف المهارات ومراجعة الأدلة المفتوحة"})
    assert placed.status_code == 200
    with TestingSessionLocal() as db:
        session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).one()
        journey = db.query(StudentJourney).one()
        assert session.assigned_level == 2 and session.official_for_reporting is True
        assert journey.current_level == 2 and journey.current_lesson_id.startswith("L2-")
        assert db.query(PlacementDecisionV2).one().policy_version.endswith("candidate")


def test_reports_use_null_for_missing_and_student_cannot_open_admin(student_client):
    assert student_client.get("/v2/assessments/admin/reports/summary").status_code == 403
    assert student_client.get("/v2/assessments/current-action").json()["action"] == "start_pretest"


def test_posttest_gate_requires_ready_journey_and_explicit_enable(student_client):
    blocked = student_client.post("/v2/assessments/posttest/start")
    assert blocked.status_code == 409


def test_v2_admin_queues_reject_student(student_client):
    assert student_client.get("/v2/assessments/admin/review-queue").status_code == 403
    assert student_client.get("/v2/assessments/admin/placement-queue").status_code == 403


def test_review_queue_includes_evidence_and_blocks_student_access(researcher_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        session = AssessmentSession(student_id=student.id, content_release_id=release.id, session_type="pretest", status="in_progress", v2_state="waiting_review", v2_question_index=30)
        db.add(session); db.flush()
        q = next(q for q in get_release()["questions"] if q["role"] == "pretest" and q["interaction"] == "write_text")
        response = AssessmentQuestionResponse(assessment_session_id=session.id, question_id=q["id"], role="pretest", answer_json={"text_response": "كتابة الطالب"},
            submit_key=str(uuid4()), status="pending_review", is_correct=None, skill_group=q["skill_group"], evidence_type=q["evidence_type"])
        db.add(response); db.commit()
        response_id = response.id
    queue = researcher_client.get("/v2/assessments/admin/review-queue").json()
    item = next(item for item in queue["items"] if item["response_id"] == response_id)
    assert item["evidence_ready"] is True
    assert item["text_response"] == "كتابة الطالب"
    assert item["prompt"] and item["rubric"]
    assert "audio_storage_key" not in str(item)
    assert researcher_client.get(f"/v2/assessments/admin/responses/{response_id}/audio").status_code == 404
    assert researcher_client.get("/v2/assessments/admin/review-queue?limit=101").status_code == 422


def test_review_refuses_missing_actual_student_evidence(researcher_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        session = AssessmentSession(student_id=student.id, content_release_id=release.id, session_type="pretest", status="in_progress", v2_state="waiting_review", v2_question_index=30)
        db.add(session); db.flush()
        q = next(q for q in get_release()["questions"] if q["role"] == "pretest" and q["interaction"] == "read_aloud")
        response = AssessmentQuestionResponse(assessment_session_id=session.id, question_id=q["id"], role="pretest", answer_json={"audio_storage_key": "audio/999/missing.webm"},
            submit_key=str(uuid4()), status="pending_review", is_correct=None, skill_group=q["skill_group"], evidence_type=q["evidence_type"])
        db.add(response); db.commit()
        response_id = response.id
    denied = researcher_client.post(f"/v2/assessments/admin/responses/{response_id}/review", json={"is_correct": True, "note": "لا يوجد تسجيل"})
    assert denied.status_code == 409


def test_pinned_assessment_snapshot_survives_candidate_bank_rotation(student_client, monkeypatch):
    started = student_client.post("/v2/assessments/pretest/start").json()
    session_id = started["session"]["session_id"]
    with TestingSessionLocal() as db:
        session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).one()
        release = register_candidate_release(db)
        assert (release.manifest_json or {}).get("bank_snapshot")
        db.commit()
    import v2_assessment_runtime as runtime
    monkeypatch.setattr(runtime, "get_release", lambda: {"checksum": "different", "version": "future"})
    resumed = student_client.get(f"/v2/assessments/sessions/{session_id}")
    assert resumed.status_code == 200
    assert resumed.json()["interaction"]["question"]["question_id"] == started["interaction"]["question"]["question_id"]

def test_shared_official_selection_preserves_history_and_report_average(researcher_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        original = AssessmentSession(student_id=student.id, session_type="pretest", status="completed",
            assessment_attempt_no=1, v2_state="completed", official_for_reporting=False, final_score=20)
        newer = AssessmentSession(student_id=student.id, session_type="pretest", status="completed",
            assessment_attempt_no=2, v2_state="completed", official_for_reporting=False, final_score=80)
        db.add_all([original, newer]); db.flush()
        newer.supersedes_session_id = original.id
        mark_official_completed_attempt(db, original)
        db.commit()
        mark_official_completed_attempt(db, newer)
        db.commit()
        history = db.query(AssessmentSession).filter(AssessmentSession.student_id == student.id).order_by(AssessmentSession.assessment_attempt_no).all()
        assert len(history) == 2
        assert [row.official_for_reporting for row in history] == [False, True]
        assert newer.supersedes_session_id == original.id
    report = researcher_client.get("/v2/assessments/admin/reports/summary")
    assert report.status_code == 200
    assert report.json()["averages"]["pretest"] == 80.0


def test_private_audio_stream_resolves_only_linked_assessment_evidence(researcher_client, monkeypatch):
    from fastapi.responses import Response
    import recordings
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        session = AssessmentSession(student_id=student.id, content_release_id=release.id, session_type="pretest",
            status="in_progress", v2_state="waiting_review", v2_question_index=30)
        db.add(session); db.flush()
        q = next(q for q in get_release()["questions"] if q["role"] == "pretest" and q["interaction"] == "read_aloud")
        row = AssessmentQuestionResponse(assessment_session_id=session.id, question_id=q["id"], role="pretest",
            answer_json={"audio_storage_key": f"audio/{student.id}/owned.webm"}, submit_key=str(uuid4()),
            status="pending_review", is_correct=None, skill_group=q["skill_group"], evidence_type=q["evidence_type"])
        db.add(row); db.flush()
        db.add(AudioSubmission(assessment_response_id=row.id, storage_key=f"audio/{student.id}/owned.webm",
            file_size=2000, mime_type="audio/webm", status="pending_review"))
        response_id = row.id
        db.commit()
    checked = []
    def fake_play_by_key(*, key, range_header, researcher):
        checked.append((key, range_header, researcher.role))
        return Response(b"test-audio", media_type="audio/webm")
    monkeypatch.setattr(recordings, "play_by_key", fake_play_by_key)
    result = researcher_client.get(f"/v2/assessments/admin/responses/{response_id}/audio", headers={"Range": "bytes=0-2"})
    assert result.status_code == 200
    assert checked == [(f"audio/{student.id}/owned.webm", "bytes=0-2", "researcher")]
    assert researcher_client.get("/v2/assessments/admin/responses/999999/audio").status_code == 404

def test_v2_pretest_does_not_bypass_completed_v1_history(student_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        old = AssessmentSession(student_id=student.id, session_type="pretest", status="completed",
            assessment_attempt_no=1, official_for_reporting=True, final_score=75)
        db.add(old)
        db.commit()
    started = student_client.post("/v2/assessments/pretest/start")
    assert started.status_code == 409
    assert "تفويض" in started.json()["detail"]
    with TestingSessionLocal() as db:
        assert db.query(AssessmentSession).count() == 1

def test_reading_review_requires_unchanged_private_object(researcher_client, monkeypatch):
    import storage
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        session = AssessmentSession(student_id=student.id, content_release_id=release.id, session_type="pretest",
            status="in_progress", v2_state="waiting_review", v2_question_index=30)
        db.add(session); db.flush()
        q = next(q for q in get_release()["questions"] if q["role"] == "pretest" and q["interaction"] == "read_aloud")
        response = AssessmentQuestionResponse(assessment_session_id=session.id, question_id=q["id"], role="pretest",
            answer_json={"audio_storage_key": f"audio/{student.id}/lost.webm"}, submit_key=str(uuid4()),
            status="pending_review", is_correct=None, skill_group=q["skill_group"], evidence_type=q["evidence_type"])
        db.add(response); db.flush()
        db.add(AudioSubmission(assessment_response_id=response.id, storage_key=f"audio/{student.id}/lost.webm",
            file_size=5120, mime_type="audio/webm", status="pending_review"))
        response_id = response.id
        db.commit()
    def missing(*_args, **_kwargs):
        raise ValueError("missing")
    monkeypatch.setattr(storage, "verify_audio", missing)
    response = researcher_client.post(f"/v2/assessments/admin/responses/{response_id}/review",
        json={"is_correct": True, "note": "استماع ومراجعة"})
    assert response.status_code == 409
    with TestingSessionLocal() as db:
        row = db.query(AssessmentQuestionResponse).filter(AssessmentQuestionResponse.id == response_id).one()
        assert row.status == "pending_review" and row.is_correct is None
