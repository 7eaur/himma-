"""A learner enrolled in V2 cannot reopen V1 academic or recording writes."""
from conftest import TestingSessionLocal
from db.adaptation_models import RewardEvent
from db.learning_models import StudentJourney
from db.models import AssessmentSession, Attempt, Student
from v2_content.importer import register_candidate_release


def test_v2_learner_cannot_start_or_write_legacy_evidence(student_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter_by(access_code="STU001").one()
        release = register_candidate_release(db)
        db.add(StudentJourney(student_id=student.id, content_release_id=release.id,
                              placement_state="placed", current_level=1, current_lesson_id="L1-01"))
        db.commit()
        student_id = student.id
    calls = [
        ("get", "/assessment/active", None),
        ("post", "/assessment/start", {"session_type":"pretest"}),
        ("post", "/assessment/session/999999/finish", None),
        ("post", "/activities/start", None),
        ("post", "/recordings/init", {"file_size": 1024, "mime_type":"audio/webm"}),
        ("post", "/recordings/complete", {"recording_id":"fake", "storage_key":f"audio/{student_id}/fake.webm"}),
        ("get", "/adaptation/status", None),
        ("get", "/rewards", None),
        ("post", "/adaptation/session/999999/prepare-next", None),
    ]
    for method, path, body in calls:
        response = getattr(student_client, method)(path, json=body) if body else getattr(student_client, method)(path)
        assert response.status_code == 409, (path, response.text)
    with TestingSessionLocal() as db:
        assert db.query(AssessmentSession).filter_by(student_id=student_id).count() == 0
        assert db.query(Attempt).count() == 0
        assert db.query(RewardEvent).filter_by(student_id=student_id).count() == 0


def test_supervisor_cannot_grant_v1_rewards_or_override_v2_journey(researcher_client):
    with TestingSessionLocal() as db:
        student = db.query(Student).filter_by(access_code="STU001").one()
        release = register_candidate_release(db)
        db.add(StudentJourney(student_id=student.id, content_release_id=release.id,
                              placement_state="placed", current_level=1, current_lesson_id="L1-01"))
        db.commit()
        student_id = student.id
    calls = [
        ("get", f"/researcher/students/{student_id}/rewards", None),
        ("post", f"/researcher/students/{student_id}/adaptation/manual-override", {"new_level":2,"reason":"سبب اختبار موثق"}),
        ("post", f"/researcher/students/{student_id}/adaptation/assign-reinforcement", {"item_id":1,"reason":"سبب اختبار موثق"}),
    ]
    for method, path, body in calls:
        response = getattr(researcher_client, method)(path, json=body) if body else getattr(researcher_client, method)(path)
        assert response.status_code == 409, (path, response.text)
    with TestingSessionLocal() as db:
        assert db.query(RewardEvent).filter_by(student_id=student_id).count() == 0
        assert db.query(Student).filter_by(id=student_id).one().current_level == 1


def test_historical_v1_student_can_still_start_old_pretest(student_client):
    response = student_client.post("/assessment/start", json={"session_type":"pretest"})
    assert response.status_code == 200, response.text
    with TestingSessionLocal() as db:
        student = db.query(Student).filter_by(access_code="STU001").one()
        assert db.query(StudentJourney).filter_by(student_id=student.id).count() == 0
        assert db.query(AssessmentSession).filter_by(student_id=student.id,session_type="pretest").count() == 1
