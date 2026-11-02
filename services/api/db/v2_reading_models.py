"""V2-only durable reading evaluation records.

These tables are not connected to student APIs until the replacement pipeline
and all academic consumers are ready for a single release cutover.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer,
    JSON, Numeric, String, UniqueConstraint, text,
)
from sqlalchemy.dialects.postgresql import JSONB

from db.models import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class V2ReadingJob(Base):
    __tablename__ = "v2_reading_jobs"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    audio_submission_id = Column(Integer, ForeignKey("audio_submissions.id", ondelete="RESTRICT"), nullable=False)
    content_release_id = Column(Integer, ForeignKey("content_releases.id", ondelete="RESTRICT"), nullable=False)
    lesson_response_id = Column(Integer, ForeignKey("lesson_question_responses.id", ondelete="CASCADE"))
    assessment_response_id = Column(Integer, ForeignKey("assessment_question_responses.id", ondelete="CASCADE"))
    question_id = Column(String(160), nullable=False)
    reference_text = Column(String, nullable=False)
    reference_sha256 = Column(String(64), nullable=False)
    reading_kind = Column(String(16), nullable=False)
    learning_mode = Column(String(16), nullable=False)
    policy_version = Column(String(80), nullable=False)
    alias_catalog_version = Column(String(80), nullable=False)

    status = Column(String(24), nullable=False, default="queued", server_default="queued")
    is_current = Column(Boolean, nullable=False, default=True, server_default="true")
    attempt_count = Column(Integer, nullable=False, default=0, server_default="0")
    max_attempts = Column(Integer, nullable=False, default=3, server_default="3")
    version = Column(Integer, nullable=False, default=1, server_default="1")
    next_attempt_at = Column(DateTime(timezone=True))
    lease_owner = Column(String(160))
    lease_expires_at = Column(DateTime(timezone=True))
    last_error_code = Column(String(100))
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    evaluated_at = Column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "(CASE WHEN lesson_response_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN assessment_response_id IS NOT NULL THEN 1 ELSE 0 END) = 1",
            name="ck_v2_reading_jobs_one_owner",
        ),
        CheckConstraint("reading_kind IN ('letter','word','sentence','text')",
                        name="ck_v2_reading_jobs_kind"),
        CheckConstraint("learning_mode IN ('training','assessment')",
                        name="ck_v2_reading_jobs_mode"),
        CheckConstraint(
            "status IN ('queued','processing','retry_wait','retry_audio','evidence_ready','service_unavailable','superseded')",
            name="ck_v2_reading_jobs_status",
        ),
        CheckConstraint("attempt_count >= 0 AND max_attempts BETWEEN 1 AND 10",
                        name="ck_v2_reading_jobs_attempts"),
        CheckConstraint("version >= 1", name="ck_v2_reading_jobs_version"),
        CheckConstraint("length(reference_sha256) = 64", name="ck_v2_reading_jobs_checksum"),
        UniqueConstraint("audio_submission_id", name="uq_v2_reading_jobs_audio"),
        Index("uq_v2_reading_jobs_current_lesson", "lesson_response_id",
              unique=True, postgresql_where=text("is_current IS TRUE"),
              sqlite_where=text("is_current IS 1")),
        Index("uq_v2_reading_jobs_current_assessment", "assessment_response_id",
              unique=True, postgresql_where=text("is_current IS TRUE"),
              sqlite_where=text("is_current IS 1")),
        Index("ix_v2_reading_jobs_claim", "status", "next_attempt_at",
              "lease_expires_at", "created_at"),
        Index("ix_v2_reading_jobs_student", "student_id", "created_at"),
    )


class V2ReadingEvaluation(Base):
    __tablename__ = "v2_reading_evaluations"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("v2_reading_jobs.id", ondelete="RESTRICT"),
                    nullable=False)
    audio_submission_id = Column(Integer, ForeignKey("audio_submissions.id", ondelete="RESTRICT"),
                                 nullable=False)
    decision = Column(String(16), nullable=False)
    score_fraction = Column(Numeric(6, 5), nullable=False)
    passed_for_progress = Column(Boolean, nullable=False)
    evidence_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    decided_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    __table_args__ = (
        UniqueConstraint("job_id", name="uq_v2_reading_evaluations_job"),
        UniqueConstraint("audio_submission_id", name="uq_v2_reading_evaluations_audio"),
        CheckConstraint("decision IN ('correct','incorrect')",
                        name="ck_v2_reading_evaluations_decision"),
        CheckConstraint("score_fraction BETWEEN 0 AND 1",
                        name="ck_v2_reading_evaluations_score"),
    )
