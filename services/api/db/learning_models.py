"""V2 journey/session state pinned to an immutable content release."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, JSON, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB

from db.models import Base


def _now():
    return datetime.now(timezone.utc)


class StudentJourney(Base):
    __tablename__ = "student_journeys"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, unique=True)
    content_release_id = Column(Integer, ForeignKey("content_releases.id", ondelete="RESTRICT"), nullable=False)
    current_level = Column(Integer, nullable=False, default=1, server_default="1")
    current_lesson_id = Column(String(20), nullable=True)
    placement_state = Column(String(32), nullable=False, default="not_started", server_default="not_started")
    status = Column(String(32), nullable=False, default="active", server_default="active")
    version = Column(Integer, nullable=False, default=1, server_default="1")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        CheckConstraint("current_level BETWEEN 1 AND 3", name="ck_student_journeys_level"),
        CheckConstraint("placement_state IN ('not_started','in_progress','placed','posttest_ready','completed')", name="ck_student_journeys_placement"),
        CheckConstraint("status IN ('active','paused','completed')", name="ck_student_journeys_status"),
        CheckConstraint("version >= 1", name="ck_student_journeys_version"),
    )


class LessonSession(Base):
    __tablename__ = "lesson_sessions"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    content_release_id = Column(Integer, ForeignKey("content_releases.id", ondelete="RESTRICT"), nullable=False)
    lesson_id = Column(String(20), nullable=False)
    stage = Column(String(32), nullable=False, default="intro", server_default="intro")
    step_index = Column(Integer, nullable=False, default=0, server_default="0")
    status = Column(String(32), nullable=False, default="in_progress", server_default="in_progress")
    video_seen = Column(Boolean, nullable=False, default=False, server_default="false")
    return_to = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    version = Column(Integer, nullable=False, default=1, server_default="1")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("stage IN ('intro','video','guided_practice','independent_check','waiting_review','complete')", name="ck_lesson_sessions_stage"),
        CheckConstraint("status IN ('in_progress','waiting_review','completed','abandoned')", name="ck_lesson_sessions_status"),
        CheckConstraint("step_index >= 0", name="ck_lesson_sessions_step"),
        CheckConstraint("version >= 1", name="ck_lesson_sessions_version"),
        Index("uq_lesson_sessions_active_student", "student_id", unique=True, postgresql_where=text("status IN ('in_progress','waiting_review')"), sqlite_where=text("status IN ('in_progress','waiting_review')")),
    )


class LessonQuestionResponse(Base):
    __tablename__ = "lesson_question_responses"

    id = Column(Integer, primary_key=True)
    lesson_session_id = Column(Integer, ForeignKey("lesson_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String(160), nullable=False)
    role = Column(String(32), nullable=False)
    answer_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    submit_key = Column(String(100), nullable=False)
    attempt_no = Column(Integer, nullable=False, default=1, server_default="1")
    status = Column(String(32), nullable=False, default="submitted", server_default="submitted")
    is_correct = Column(Boolean, nullable=True)
    hint_used = Column(Boolean, nullable=False, default=False, server_default="false")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("role IN ('guided_practice','independent_check','support_check')", name="ck_lesson_responses_role"),
        CheckConstraint("status IN ('submitted','pending_review','graded')", name="ck_lesson_responses_status"),
        CheckConstraint("attempt_no >= 1", name="ck_lesson_responses_attempt"),
        UniqueConstraint("lesson_session_id", "question_id", "attempt_no", name="uq_lesson_response_question_attempt"),
        UniqueConstraint("lesson_session_id", "submit_key", name="uq_lesson_response_submit_key"),
    )
