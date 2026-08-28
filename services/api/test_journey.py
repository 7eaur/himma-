"""M04 regression tests for the student-facing L1 -> L2 -> L3 journey."""

from datetime import datetime, timezone

import seed
from conftest import TestingSessionLocal
from db.models import AssessmentSession, Attempt, ContentItem, Student


def _complete_level(db, student_id: int, level_id: int) -> AssessmentSession:
    session = AssessmentSession(
        student_id=student_id,
        session_type="core",
        status="completed",
        assigned_level=level_id,
        completed_at=datetime.now(timezone.utc),
    )
    db.add(session)
    db.flush()
    items = (
        db.query(ContentItem)
        .filter(
            ContentItem.kind == "core_activity",
            ContentItem.level_id == level_id,
        )
        .order_by(ContentItem.order_index)
        .all()
    )
    assert len(items) == 10
    for item in items:
        db.add(
            Attempt(
                session_id=session.id,
                item_id=item.id,
                status="completed",
                completed_at=datetime.now(timezone.utc),
            )
        )
    db.flush()
    return session


def test_journey_is_locked_before_pretest(student_client):
    response = student_client.get("/journey")
    assert response.status_code == 200
    data = response.json()
    assert data["pretest_completed"] is False
    assert data["starting_level"] is None
    assert [level["state"] for level in data["levels"]] == ["locked", "locked", "locked"]
    assert data["learning_journey_completed"] is False
    assert data["posttest_ready"] is False


def test_journey_distinguishes_skipped_completed_and_active_levels(student_client):
    seed.run_seed()
    db = TestingSessionLocal()
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    student.current_level = 3
    db.add(
        AssessmentSession(
            student_id=student.id,
            session_type="pretest",
            status="completed",
            assigned_level=2,
            final_score=75,
            completed_at=datetime.now(timezone.utc),
        )
    )
    _complete_level(db, student.id, 2)
    level3 = AssessmentSession(
        student_id=student.id,
        session_type="core",
        status="in_progress",
        assigned_level=3,
    )
    db.add(level3)
    db.commit()
    db.close()

    response = student_client.get("/journey")
    assert response.status_code == 200
    data = response.json()
    assert data["starting_level"] == 2
    assert data["current_level"] == 3
    assert [level["state"] for level in data["levels"]] == ["skipped", "completed", "active"]
    assert data["levels"][1]["completed_items"] == 10
    assert data["levels"][2]["completed_items"] == 0
    assert data["learning_journey_completed"] is False


def test_posttest_ready_only_after_completed_level_three_and_supervisor_enable(student_client):
    seed.run_seed()
    db = TestingSessionLocal()
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    student.current_level = 3
    student.posttest_enabled = True
    db.add(
        AssessmentSession(
            student_id=student.id,
            session_type="pretest",
            status="completed",
            assigned_level=3,
            final_score=90,
            completed_at=datetime.now(timezone.utc),
        )
    )
    _complete_level(db, student.id, 3)
    db.commit()
    db.close()

    response = student_client.get("/journey")
    assert response.status_code == 200
    data = response.json()
    assert [level["state"] for level in data["levels"]] == ["skipped", "skipped", "completed"]
    assert data["learning_journey_completed"] is True
    assert data["posttest_ready"] is True
