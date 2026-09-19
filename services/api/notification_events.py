"""Domain-event materialization for the supervisor notification inbox.

Notifications are projections of durable domain state. They are created or
resolved in the same transaction as the state transition that makes them
relevant; HTTP GET handlers remain strictly read-only.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import event, inspect, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from db.models import AssessmentSession, Attempt, AttemptResponse, AudioSubmission, Student
from db.notification_models import ResearcherNotification
from db.reinforcement_models import ReinforcementCycle


def _insert_notification(connection, values: dict) -> None:
    """Insert one durable notification without opening a nested transaction."""
    dialect = connection.dialect.name
    if dialect == "postgresql":
        statement = (
            pg_insert(ResearcherNotification)
            .values(**values)
            .on_conflict_do_nothing(index_elements=[ResearcherNotification.dedupe_key])
        )
        connection.execute(statement)
        return
    if dialect == "sqlite":
        statement = (
            sqlite_insert(ResearcherNotification)
            .values(**values)
            .on_conflict_do_nothing(index_elements=[ResearcherNotification.dedupe_key])
        )
        connection.execute(statement)
        return

    existing = connection.execute(
        select(ResearcherNotification.id).where(
            ResearcherNotification.dedupe_key == values["dedupe_key"],
        )
    ).first()
    if existing is None:
        connection.execute(insert(ResearcherNotification).values(**values))


def _student_for_audio_response(connection, response_id: int):
    return connection.execute(
        select(Student.id, Student.name)
        .select_from(AttemptResponse)
        .join(Attempt, Attempt.id == AttemptResponse.attempt_id)
        .join(AssessmentSession, AssessmentSession.id == Attempt.session_id)
        .join(Student, Student.id == AssessmentSession.student_id)
        .where(AttemptResponse.id == response_id)
    ).first()


def _student(connection, student_id: int):
    return connection.execute(
        select(Student.id, Student.name).where(Student.id == student_id)
    ).first()


def _audio_notification_values(submission: AudioSubmission, student) -> dict:
    return {
        "dedupe_key": f"audio-review:{submission.id}",
        "notification_type": "audio_review_required",
        "title": "تسجيل جديد يحتاج مراجعة",
        "message": f"لدى {student.name} تسجيل قراءة بانتظار المراجعة.",
        "href": f"/admin/audio-review?submission_id={submission.id}&student_id={student.id}",
        "entity_type": "audio_submission",
        "entity_id": str(submission.id),
        "is_read": False,
        "created_at": datetime.now(timezone.utc),
        "read_at": None,
    }


def _reinforcement_notification_values(cycle: ReinforcementCycle, student) -> dict:
    return {
        "dedupe_key": f"reinforcement-escalated:{cycle.id}",
        "notification_type": "reinforcement_attention",
        "title": "طالب يحتاج متابعة",
        "message": f"وصلت تقوية {student.name} إلى حالة تحتاج تدخل المشرف.",
        "href": f"/admin/students/{student.id}",
        "entity_type": "reinforcement_cycle",
        "entity_id": str(cycle.id),
        "is_read": False,
        "created_at": datetime.now(timezone.utc),
        "read_at": None,
    }


@event.listens_for(AudioSubmission, "after_insert")
def _audio_submission_inserted(mapper, connection, target: AudioSubmission) -> None:
    if target.status != "uploaded":
        return
    student = _student_for_audio_response(connection, target.response_id)
    if student is not None:
        _insert_notification(connection, _audio_notification_values(target, student))


@event.listens_for(AudioSubmission, "after_update")
def _audio_submission_updated(mapper, connection, target: AudioSubmission) -> None:
    history = inspect(target).attrs.status.history
    if not history.has_changes():
        return
    if target.status == "uploaded":
        student = _student_for_audio_response(connection, target.response_id)
        if student is not None:
            _insert_notification(connection, _audio_notification_values(target, student))
        return

    connection.execute(
        update(ResearcherNotification)
        .where(
            ResearcherNotification.dedupe_key == f"audio-review:{target.id}",
            ResearcherNotification.is_read.is_(False),
        )
        .values(is_read=True, read_at=datetime.now(timezone.utc))
    )


@event.listens_for(ReinforcementCycle, "after_insert")
def _reinforcement_cycle_inserted(mapper, connection, target: ReinforcementCycle) -> None:
    if target.status != "escalated":
        return
    student = _student(connection, target.student_id)
    if student is not None:
        _insert_notification(connection, _reinforcement_notification_values(target, student))


@event.listens_for(ReinforcementCycle, "after_update")
def _reinforcement_cycle_updated(mapper, connection, target: ReinforcementCycle) -> None:
    history = inspect(target).attrs.status.history
    if not history.has_changes() or target.status != "escalated":
        return
    student = _student(connection, target.student_id)
    if student is not None:
        _insert_notification(connection, _reinforcement_notification_values(target, student))
