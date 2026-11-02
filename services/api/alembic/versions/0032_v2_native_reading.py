"""Create the V2 native speech evidence queue without modifying existing grades.

Revision ID: 0032_v2_native_reading
Revises: 0031_v2_reading_only

This migration only adds nullable fractional-score fields and isolated records.
Historical human reviews and all stored audio remain intact.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0032_v2_native_reading"
down_revision = "0031_v2_reading_only"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("lesson_question_responses",
                  sa.Column("question_score_fraction", sa.Numeric(6, 5), nullable=True))
    op.add_column("assessment_question_responses",
                  sa.Column("question_score_fraction", sa.Numeric(6, 5), nullable=True))
    op.create_check_constraint(
        "ck_lesson_responses_fraction", "lesson_question_responses",
        "question_score_fraction IS NULL OR (question_score_fraction BETWEEN 0 AND 1)")
    op.create_check_constraint(
        "ck_assessment_responses_fraction", "assessment_question_responses",
        "question_score_fraction IS NULL OR (question_score_fraction BETWEEN 0 AND 1)")

    op.create_table(
        "v2_reading_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("audio_submission_id", sa.Integer(),
                  sa.ForeignKey("audio_submissions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("content_release_id", sa.Integer(),
                  sa.ForeignKey("content_releases.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("lesson_response_id", sa.Integer(),
                  sa.ForeignKey("lesson_question_responses.id", ondelete="CASCADE")),
        sa.Column("assessment_response_id", sa.Integer(),
                  sa.ForeignKey("assessment_question_responses.id", ondelete="CASCADE")),
        sa.Column("question_id", sa.String(160), nullable=False),
        sa.Column("reference_text", sa.String(), nullable=False),
        sa.Column("reference_sha256", sa.String(64), nullable=False),
        sa.Column("reading_kind", sa.String(16), nullable=False),
        sa.Column("learning_mode", sa.String(16), nullable=False),
        sa.Column("policy_version", sa.String(80), nullable=False),
        sa.Column("alias_catalog_version", sa.String(80), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="queued"),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True)),
        sa.Column("lease_owner", sa.String(160)),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True)),
        sa.Column("last_error_code", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "(CASE WHEN lesson_response_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN assessment_response_id IS NOT NULL THEN 1 ELSE 0 END) = 1",
            name="ck_v2_reading_jobs_one_owner"),
        sa.CheckConstraint("reading_kind IN ('letter','word','sentence','text')",
                           name="ck_v2_reading_jobs_kind"),
        sa.CheckConstraint("learning_mode IN ('training','assessment')",
                           name="ck_v2_reading_jobs_mode"),
        sa.CheckConstraint(
            "status IN ('queued','processing','retry_wait','retry_audio','evidence_ready','service_unavailable','superseded')",
            name="ck_v2_reading_jobs_status"),
        sa.CheckConstraint("attempt_count >= 0 AND max_attempts BETWEEN 1 AND 10",
                           name="ck_v2_reading_jobs_attempts"),
        sa.CheckConstraint("version >= 1", name="ck_v2_reading_jobs_version"),
        sa.CheckConstraint("length(reference_sha256) = 64",
                           name="ck_v2_reading_jobs_checksum"),
        sa.UniqueConstraint("audio_submission_id", name="uq_v2_reading_jobs_audio"),
    )
    op.create_index("uq_v2_reading_jobs_current_lesson", "v2_reading_jobs",
                    ["lesson_response_id"], unique=True,
                    postgresql_where=sa.text("is_current IS TRUE"))
    op.create_index("uq_v2_reading_jobs_current_assessment", "v2_reading_jobs",
                    ["assessment_response_id"], unique=True,
                    postgresql_where=sa.text("is_current IS TRUE"))
    op.create_index("ix_v2_reading_jobs_claim", "v2_reading_jobs",
                    ["status", "next_attempt_at", "lease_expires_at", "created_at"])
    op.create_index("ix_v2_reading_jobs_student", "v2_reading_jobs",
                    ["student_id", "created_at"])

    op.create_table(
        "v2_reading_evaluations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.Integer(),
                  sa.ForeignKey("v2_reading_jobs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("audio_submission_id", sa.Integer(),
                  sa.ForeignKey("audio_submissions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("decision", sa.String(16), nullable=False),
        sa.Column("score_fraction", sa.Numeric(6, 5), nullable=False),
        sa.Column("passed_for_progress", sa.Boolean(), nullable=False),
        sa.Column("evidence_json", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"),
                  nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("job_id", name="uq_v2_reading_evaluations_job"),
        sa.UniqueConstraint("audio_submission_id", name="uq_v2_reading_evaluations_audio"),
        sa.CheckConstraint("decision IN ('correct','incorrect')",
                           name="ck_v2_reading_evaluations_decision"),
        sa.CheckConstraint("score_fraction BETWEEN 0 AND 1",
                           name="ck_v2_reading_evaluations_score"),
    )


def downgrade():
    # Refuse a destructive rollback once real speech evidence is present.
    db = op.get_bind()
    if db.execute(sa.text("SELECT count(*) FROM v2_reading_jobs")).scalar_one():
        raise RuntimeError(
            "Native V2 reading jobs exist; use an authorized data-preserving "
            "application rollback instead of dropping student audio evidence")
    if db.execute(sa.text("SELECT count(*) FROM v2_reading_evaluations")).scalar_one():
        raise RuntimeError("Cannot discard V2 reading evaluation history")
    op.drop_table("v2_reading_evaluations")
    op.drop_index("ix_v2_reading_jobs_student", table_name="v2_reading_jobs")
    op.drop_index("ix_v2_reading_jobs_claim", table_name="v2_reading_jobs")
    op.drop_index("uq_v2_reading_jobs_current_assessment", table_name="v2_reading_jobs")
    op.drop_index("uq_v2_reading_jobs_current_lesson", table_name="v2_reading_jobs")
    op.drop_table("v2_reading_jobs")
    op.drop_constraint("ck_assessment_responses_fraction",
                       "assessment_question_responses", type_="check")
    op.drop_constraint("ck_lesson_responses_fraction",
                       "lesson_question_responses", type_="check")
    op.drop_column("assessment_question_responses", "question_score_fraction")
    op.drop_column("lesson_question_responses", "question_score_fraction")
