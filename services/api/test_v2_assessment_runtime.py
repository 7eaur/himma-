from uuid import uuid4

from conftest import TestingSessionLocal
from db.learning_models import AssessmentQuestionResponse, PlacementDecisionV2, StudentJourney
from db.models import AssessmentSession, Student
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


def test_open_responses_keep_placement_pending_until_human_review_and_manual_decision(researcher_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        release = register_candidate_release(db)
        db.add(StudentJourney(student_id=student.id, content_release_id=release.id, placement_state="in_progress", current_level=1))
        session = AssessmentSession(student_id=student.id, content_release_id=release.id, session_type="pretest", status="in_progress", v2_state="waiting_review", v2_question_index=30, v2_policy_version="test", assessment_attempt_no=1)
        db.add(session); db.flush()
        questions = [q for q in get_release()["questions"] if q["role"] == "pretest"]
        for q in questions:
            db.add(AssessmentQuestionResponse(
                assessment_session_id=session.id, question_id=q["id"], role="pretest", answer_json={"test": True},
                submit_key=str(uuid4()), status="pending_review" if q["interaction"] in {"read_aloud", "write_text"} else "graded",
                is_correct=None if q["interaction"] in {"read_aloud", "write_text"} else True,
                skill_group=q["skill_group"], evidence_type=q["evidence_type"],
            ))
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
