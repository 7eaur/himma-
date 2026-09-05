"""Manual adaptation override integrity scenarios."""

from datetime import datetime, timezone

import seed
from conftest import TestingSessionLocal
from db.models import AssessmentSession, Attempt, ContentItem, Student


def test_manual_override_transitions_active_core_session_and_preserves_history(researcher_client):
    seed.run_seed()
    db = TestingSessionLocal()
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    student.current_level = 1
    session = AssessmentSession(
        student_id=student.id,
        session_type="core",
        status="in_progress",
        assigned_level=1,
    )
    db.add(session)
    db.flush()
    item = (
        db.query(ContentItem)
        .filter(ContentItem.kind == "core_activity", ContentItem.level_id == 1)
        .order_by(ContentItem.order_index)
        .first()
    )
    attempt = Attempt(
        session_id=session.id,
        item_id=item.id,
        status="completed",
        completed_at=datetime.now(timezone.utc),
    )
    db.add(attempt)
    db.commit()
    student_id = student.id
    old_session_id = session.id
    attempt_id = attempt.id
    db.close()

    response = researcher_client.post(
        f"/researcher/students/{student_id}/adaptation/manual-override",
        json={"new_level": 2, "reason": "تعديل مستوى موثق لاختبار سلامة المسار"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["previous_level"] == 1
    assert payload["new_level"] == 2
    assert payload["explanation"]["manual_session_transition"] is True
    assert payload["explanation"]["previous_session_id"] == old_session_id

    db = TestingSessionLocal()
    try:
        student = db.query(Student).filter(Student.id == student_id).one()
        old_session = db.query(AssessmentSession).filter(AssessmentSession.id == old_session_id).one()
        preserved_attempt = db.query(Attempt).filter(Attempt.id == attempt_id).one()
        active = db.query(AssessmentSession).filter(
            AssessmentSession.student_id == student_id,
            AssessmentSession.status == "in_progress",
        ).one()

        assert student.current_level == 2
        assert old_session.status == "completed"
        assert old_session.assigned_level == 1
        assert preserved_attempt.session_id == old_session_id
        assert active.session_type == "core"
        assert active.assigned_level == 2
        assert active.id == payload["explanation"]["next_session_id"]
    finally:
        db.close()


def test_manual_override_is_rejected_while_assessment_is_active(researcher_client):
    seed.run_seed()
    db = TestingSessionLocal()
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    student.current_level = 1
    db.add(AssessmentSession(
        student_id=student.id,
        session_type="pretest",
        status="in_progress",
        assigned_level=1,
    ))
    db.commit()
    student_id = student.id
    db.close()

    response = researcher_client.post(
        f"/researcher/students/{student_id}/adaptation/manual-override",
        json={"new_level": 2, "reason": "محاولة تغيير أثناء اختبار نشط"},
    )
    assert response.status_code == 409
    assert "اختبار نشط" in response.json()["detail"]
