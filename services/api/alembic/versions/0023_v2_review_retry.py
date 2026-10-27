"""Add versioned, private rerecord/rewrite tasks without altering originals.

Revision ID: 0023_v2_review_retry
Revises: 0022_v2_lesson_review
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0023_v2_review_retry"
down_revision = "0022_v2_lesson_review"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "v2_review_retry_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lesson_response_id", sa.Integer(), sa.ForeignKey("lesson_question_responses.id", ondelete="CASCADE"), nullable=True),
        sa.Column("assessment_response_id", sa.Integer(), sa.ForeignKey("assessment_question_responses.id", ondelete="CASCADE"), nullable=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requested_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("request_kind", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="requested"),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("replacement_json", sa.JSON().with_variant(JSONB(), "postgresql"), nullable=True),
        sa.Column("audio_submission_id", sa.Integer(), sa.ForeignKey("audio_submissions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("submit_key", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("(CASE WHEN lesson_response_id IS NOT NULL THEN 1 ELSE 0 END + CASE WHEN assessment_response_id IS NOT NULL THEN 1 ELSE 0 END) = 1", name="ck_v2_retry_exactly_one_owner"),
        sa.CheckConstraint("request_kind IN ('rerecord','rewrite')", name="ck_v2_retry_kind"),
        sa.CheckConstraint("status IN ('requested','submitted','superseded','resolved')", name="ck_v2_retry_status"),
    )
    op.create_index("uq_v2_retry_active_lesson", "v2_review_retry_tasks", ["lesson_response_id"], unique=True,
                    postgresql_where=sa.text("lesson_response_id IS NOT NULL AND status IN ('requested','submitted')"),
                    sqlite_where=sa.text("lesson_response_id IS NOT NULL AND status IN ('requested','submitted')"))
    op.create_index("uq_v2_retry_active_assessment", "v2_review_retry_tasks", ["assessment_response_id"], unique=True,
                    postgresql_where=sa.text("assessment_response_id IS NOT NULL AND status IN ('requested','submitted')"),
                    sqlite_where=sa.text("assessment_response_id IS NOT NULL AND status IN ('requested','submitted')"))
    op.create_index("ix_v2_retry_student_state", "v2_review_retry_tasks", ["student_id", "status"])


def downgrade():
    op.drop_index("ix_v2_retry_student_state", table_name="v2_review_retry_tasks")
    op.drop_index("uq_v2_retry_active_assessment", table_name="v2_review_retry_tasks")
    op.drop_index("uq_v2_retry_active_lesson", table_name="v2_review_retry_tasks")
    op.drop_table("v2_review_retry_tasks")
