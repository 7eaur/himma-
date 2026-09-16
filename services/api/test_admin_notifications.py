from datetime import datetime, timezone

from sqlalchemy import event

from conftest import TestingSessionLocal, engine
from db.adaptation_models import AdaptationDecision
from db.models import (
    AssessmentSession,
    Attempt,
    AttemptResponse,
    AudioSubmission,
    ContentItem,
    ContentStep,
    Skill,
    Student,
)
from db.notification_models import ResearcherNotification
from db.reinforcement_models import ReinforcementCycle


def _insert_notification(dedupe_key: str = "test:notification:1") -> int:
    db = TestingSessionLocal()
    try:
        row = ResearcherNotification(
            notification_type="test_attention",
            title="عنصر يحتاج متابعة",
            message="إشعار اختباري للمشرف.",
            href="/admin/students",
            entity_type="student",
            entity_id="1",
            dedupe_key=dedupe_key,
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row.id
    finally:
        db.close()


def _create_learning_evidence(db):
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    skill = Skill(
        skill_key="NOTIFY-SKILL",
        name="مهارة اختبار الإشعارات",
        level_id=1,
        canonical_skill_id="NOTIFY-SKILL",
    )
    db.add(skill)
    db.flush()
    item = ContentItem(
        stable_key="NOTIFY-ITEM",
        kind="core_activity",
        level_id=1,
        skill_id=skill.id,
        interaction_type="read_aloud",
        order_index=1,
        version="test-notifications",
        status="published",
        checksum="0" * 64,
        template_data={},
    )
    db.add(item)
    db.flush()
    step = ContentStep(
        item_id=item.id,
        order_index=1,
        prompt_text="اقرأ",
        expected_reading_text="ب",
    )
    db.add(step)
    db.flush()
    session = AssessmentSession(
        student_id=student.id,
        session_type="core",
        status="in_progress",
        assigned_level=1,
    )
    db.add(session)
    db.flush()
    attempt = Attempt(session_id=session.id, item_id=item.id, status="in_progress")
    db.add(attempt)
    db.flush()
    response = AttemptResponse(attempt_id=attempt.id, step_id=step.id, is_correct=None)
    db.add(response)
    db.flush()
    return student, skill, item, step, session, attempt, response


def test_notification_inbox_persists_unread_and_mark_read(researcher_client):
    notification_id = _insert_notification()
    response = researcher_client.get("/researcher/notifications")
    assert response.status_code == 200
    payload = response.json()
    assert payload["unread_count"] == 1
    item = next(value for value in payload["items"] if value["id"] == notification_id)
    assert item["is_read"] is False
    assert item["href"] == "/admin/students"

    read_response = researcher_client.post(f"/researcher/notifications/{notification_id}/read")
    assert read_response.status_code == 200
    assert read_response.json()["is_read"] is True

    replay = researcher_client.post(f"/researcher/notifications/{notification_id}/read")
    assert replay.status_code == 200
    assert replay.json()["is_read"] is True

    refreshed = researcher_client.get("/researcher/notifications").json()
    assert refreshed["unread_count"] == 0


def test_notification_read_all_is_idempotent(researcher_client):
    _insert_notification("test:notification:a")
    _insert_notification("test:notification:b")
    first = researcher_client.post("/researcher/notifications/read-all")
    assert first.status_code == 200
    assert first.json()["updated"] == 2
    second = researcher_client.post("/researcher/notifications/read-all")
    assert second.status_code == 200
    assert second.json()["updated"] == 0


def test_audio_transition_materializes_and_resolves_notification_without_get():
    db = TestingSessionLocal()
    try:
        student, skill, item, step, session, attempt, response = _create_learning_evidence(db)
        submission = AudioSubmission(
            response_id=response.id,
            storage_key="notifications/audio.webm",
            file_size=512,
            mime_type="audio/webm",
            status="uploaded",
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)

        notification = db.query(ResearcherNotification).filter(
            ResearcherNotification.dedupe_key == f"audio-review:{submission.id}"
        ).one()
        assert notification.is_read is False
        assert notification.entity_id == str(submission.id)
        assert student.name in notification.message

        submission.status = "graded"
        db.commit()
        db.expire_all()
        resolved = db.query(ResearcherNotification).filter(
            ResearcherNotification.dedupe_key == f"audio-review:{submission.id}"
        ).one()
        assert resolved.is_read is True
        assert resolved.read_at is not None
    finally:
        db.close()


def test_reinforcement_escalation_materializes_once():
    db = TestingSessionLocal()
    try:
        student, skill, item, step, session, attempt, response = _create_learning_evidence(db)
        decision = AdaptationDecision(
            student_id=student.id,
            decision_source="automatic",
            action="support",
            mastery_score=0.25,
            previous_level=1,
            new_level=1,
            weakest_skill_id=skill.id,
            recommended_item_id=item.id,
            valid_attempt_count=1,
            consecutive_low_count=1,
            snapshot_key="notify-reinforcement",
            explanation={"source": "notification-test"},
        )
        db.add(decision)
        db.flush()
        cycle = ReinforcementCycle(
            student_id=student.id,
            session_id=session.id,
            decision_id=decision.id,
            source_attempt_id=attempt.id,
            source_step_ids=[step.id],
            reinforcement_item_id=item.id,
            status="reinforcement_pending",
        )
        db.add(cycle)
        db.commit()
        db.refresh(cycle)
        assert db.query(ResearcherNotification).filter(
            ResearcherNotification.dedupe_key == f"reinforcement-escalated:{cycle.id}"
        ).count() == 0

        cycle.status = "escalated"
        cycle.escalation_reason = "test"
        db.commit()
        assert db.query(ResearcherNotification).filter(
            ResearcherNotification.dedupe_key == f"reinforcement-escalated:{cycle.id}"
        ).count() == 1

        cycle.escalation_reason = "test-updated"
        db.commit()
        assert db.query(ResearcherNotification).filter(
            ResearcherNotification.dedupe_key == f"reinforcement-escalated:{cycle.id}"
        ).count() == 1
    finally:
        db.close()


def test_notification_get_is_read_only(researcher_client):
    _insert_notification("test:read-only")
    writes: list[str] = []

    def capture_write(connection, cursor, statement, parameters, context, executemany):
        normalized = statement.lstrip().upper()
        if normalized.startswith(("INSERT", "UPDATE", "DELETE")):
            writes.append(statement)

    event.listen(engine, "before_cursor_execute", capture_write)
    try:
        response = researcher_client.get("/researcher/notifications")
    finally:
        event.remove(engine, "before_cursor_execute", capture_write)

    assert response.status_code == 200
    assert writes == []
