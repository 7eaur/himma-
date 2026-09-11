"""W3 regression coverage for the supervisor journey projection."""

from db.database import SessionLocal
from db.models import Student


def test_supervisor_journey_uses_canonical_evidence_not_current_level_pointer(researcher_client):
    created = researcher_client.post(
        "/researcher/students",
        json={"full_name": "طالب مسار W3", "grade_level": 3},
    )
    assert created.status_code == 201
    student_id = created.json()["id"]

    # Simulate a stale/historical level pointer. The Admin projection must not
    # translate this into invented completion evidence.
    db = SessionLocal()
    student = db.query(Student).filter(Student.id == student_id).one()
    student.current_level = 3
    db.commit()
    db.close()

    response = researcher_client.get(f"/researcher/students/{student_id}/journey")
    assert response.status_code == 200
    payload = response.json()
    assert payload["pretest_completed"] is False
    assert payload["current_level"] == 3
    assert [level["state"] for level in payload["levels"]] == ["locked", "locked", "locked"]
    assert payload["learning_journey_completed"] is False


def test_supervisor_journey_requires_researcher_role(student_client):
    response = student_client.get("/researcher/students/1/journey")
    assert response.status_code == 403
