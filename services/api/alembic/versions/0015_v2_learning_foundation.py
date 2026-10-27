"""Add immutable V2 release pins and resumable learning state.

Revision ID: 0015_v2_learning_foundation
Revises: 0014_reward_attempt_history
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0015_v2_learning_foundation"
down_revision = "0014_reward_attempt_history"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("content_releases", sa.Column("checksum", sa.String(64), nullable=True))
    op.add_column("content_releases", sa.Column("schema_version", sa.String(100), nullable=True))
    op.add_column("content_releases", sa.Column("status", sa.String(32), server_default="legacy_published", nullable=False))
    op.add_column("content_releases", sa.Column("manifest_json", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=True))
    op.add_column("content_releases", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("content_releases", sa.Column("is_immutable", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("assessment_sessions", sa.Column("content_release_id", sa.Integer(), nullable=True))
    op.create_foreign_key("assessment_sessions_content_release_id_fkey", "assessment_sessions", "content_releases", ["content_release_id"], ["id"], ondelete="RESTRICT")

    op.create_table(
        "student_journeys",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("content_release_id", sa.Integer(), nullable=False),
        sa.Column("current_level", sa.Integer(), server_default="1", nullable=False),
        sa.Column("current_lesson_id", sa.String(20), nullable=True),
        sa.Column("placement_state", sa.String(32), server_default="not_started", nullable=False),
        sa.Column("status", sa.String(32), server_default="active", nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("current_level BETWEEN 1 AND 3", name="ck_student_journeys_level"),
        sa.CheckConstraint("placement_state IN ('not_started','in_progress','placed','posttest_ready','completed')", name="ck_student_journeys_placement"),
        sa.CheckConstraint("status IN ('active','paused','completed')", name="ck_student_journeys_status"),
        sa.CheckConstraint("version >= 1", name="ck_student_journeys_version"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["content_release_id"], ["content_releases.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("student_id"),
    )
    op.create_table(
        "lesson_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("content_release_id", sa.Integer(), nullable=False),
        sa.Column("lesson_id", sa.String(20), nullable=False),
        sa.Column("stage", sa.String(32), server_default="intro", nullable=False),
        sa.Column("step_index", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(32), server_default="in_progress", nullable=False),
        sa.Column("video_seen", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("return_to", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("stage IN ('intro','video','guided_practice','independent_check','waiting_review','complete')", name="ck_lesson_sessions_stage"),
        sa.CheckConstraint("status IN ('in_progress','waiting_review','completed','abandoned')", name="ck_lesson_sessions_status"),
        sa.CheckConstraint("step_index >= 0", name="ck_lesson_sessions_step"),
        sa.CheckConstraint("version >= 1", name="ck_lesson_sessions_version"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["content_release_id"], ["content_releases.id"], ondelete="RESTRICT"),
    )
    op.create_index("uq_lesson_sessions_active_student", "lesson_sessions", ["student_id"], unique=True, postgresql_where=sa.text("status IN ('in_progress','waiting_review')"), sqlite_where=sa.text("status IN ('in_progress','waiting_review')"))
    op.create_table(
        "lesson_question_responses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lesson_session_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.String(160), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("answer_json", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("submit_key", sa.String(100), nullable=False),
        sa.Column("attempt_no", sa.Integer(), server_default="1", nullable=False),
        sa.Column("status", sa.String(32), server_default="submitted", nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("hint_used", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("role IN ('guided_practice','independent_check','support_check')", name="ck_lesson_responses_role"),
        sa.CheckConstraint("status IN ('submitted','pending_review','graded')", name="ck_lesson_responses_status"),
        sa.CheckConstraint("attempt_no >= 1", name="ck_lesson_responses_attempt"),
        sa.ForeignKeyConstraint(["lesson_session_id"], ["lesson_sessions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("lesson_session_id", "question_id", "attempt_no", name="uq_lesson_response_question_attempt"),
        sa.UniqueConstraint("lesson_session_id", "submit_key", name="uq_lesson_response_submit_key"),
    )


def downgrade():
    op.drop_table("lesson_question_responses")
    op.drop_index("uq_lesson_sessions_active_student", table_name="lesson_sessions")
    op.drop_table("lesson_sessions")
    op.drop_table("student_journeys")
    op.drop_constraint("assessment_sessions_content_release_id_fkey", "assessment_sessions", type_="foreignkey")
    op.drop_column("assessment_sessions", "content_release_id")
    for column in ("is_immutable", "approved_at", "manifest_json", "status", "schema_version", "checksum"):
        op.drop_column("content_releases", column)
