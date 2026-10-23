"""Add P06 V2 assessment, review and manual placement state.

Revision ID: 0019_v2_assessment_runtime
Revises: 0018_v2_adaptation_support
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0019_v2_assessment_runtime"
down_revision = "0018_v2_adaptation_support"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("assessment_sessions", sa.Column("v2_question_index", sa.Integer(), server_default="0", nullable=False))
    op.add_column("assessment_sessions", sa.Column("v2_state", sa.String(40), nullable=True))
    op.add_column("assessment_sessions", sa.Column("v2_result_json", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=True))
    op.add_column("assessment_sessions", sa.Column("v2_policy_version", sa.String(100), nullable=True))
    op.create_check_constraint("ck_assessment_sessions_v2_question_index", "assessment_sessions", "v2_question_index >= 0")
    op.create_check_constraint("ck_assessment_sessions_v2_state", "assessment_sessions", "v2_state IS NULL OR v2_state IN ('answering','waiting_review','placement_pending_review','completed')")

    op.create_table(
        "assessment_question_responses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("assessment_session_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.String(160), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("answer_json", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("submit_key", sa.String(100), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("skill_group", sa.String(10), nullable=False),
        sa.Column("evidence_type", sa.String(80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("review_note", sa.String(), nullable=True),
        sa.CheckConstraint("role IN ('pretest','posttest')", name="ck_assessment_responses_role"),
        sa.CheckConstraint("status IN ('pending_review','graded')", name="ck_assessment_responses_status"),
        sa.ForeignKeyConstraint(["assessment_session_id"], ["assessment_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("assessment_session_id", "question_id", name="uq_assessment_response_question"),
        sa.UniqueConstraint("assessment_session_id", "submit_key", name="uq_assessment_response_submit"),
    )
    op.create_index("ix_assessment_responses_review", "assessment_question_responses", ["status", "role", "created_at"])
    op.create_table(
        "assessment_question_drafts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("assessment_session_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.String(160), nullable=False),
        sa.Column("draft_json", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("version >= 1", name="ck_assessment_question_draft_version"),
        sa.ForeignKeyConstraint(["assessment_session_id"], ["assessment_sessions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("assessment_session_id", "question_id", name="uq_assessment_question_draft"),
    )
    op.create_table(
        "placement_decisions_v2",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("assessment_session_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("content_release_id", sa.Integer(), nullable=False),
        sa.Column("assigned_level", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("policy_version", sa.String(100), nullable=False),
        sa.Column("decided_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("assigned_level BETWEEN 1 AND 3", name="ck_placement_v2_level"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assessment_session_id"], ["assessment_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["content_release_id"], ["content_releases.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["decided_by"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_placement_v2_student_created", "placement_decisions_v2", ["student_id", "created_at"])

    op.drop_constraint("ck_audio_submissions_one_response_owner", "audio_submissions", type_="check")
    op.add_column("audio_submissions", sa.Column("assessment_response_id", sa.Integer(), nullable=True))
    op.create_foreign_key("audio_submissions_assessment_response_id_fkey", "audio_submissions", "assessment_question_responses", ["assessment_response_id"], ["id"], ondelete="CASCADE")
    op.create_check_constraint("ck_audio_submissions_one_response_owner", "audio_submissions", "(CASE WHEN response_id IS NOT NULL THEN 1 ELSE 0 END + CASE WHEN lesson_response_id IS NOT NULL THEN 1 ELSE 0 END + CASE WHEN assessment_response_id IS NOT NULL THEN 1 ELSE 0 END) = 1")


def downgrade():
    op.drop_constraint("ck_audio_submissions_one_response_owner", "audio_submissions", type_="check")
    op.drop_constraint("audio_submissions_assessment_response_id_fkey", "audio_submissions", type_="foreignkey")
    op.drop_column("audio_submissions", "assessment_response_id")
    op.create_check_constraint("ck_audio_submissions_one_response_owner", "audio_submissions", "(response_id IS NOT NULL AND lesson_response_id IS NULL) OR (response_id IS NULL AND lesson_response_id IS NOT NULL)")
    op.drop_index("ix_placement_v2_student_created", table_name="placement_decisions_v2")
    op.drop_table("placement_decisions_v2")
    op.drop_table("assessment_question_drafts")
    op.drop_index("ix_assessment_responses_review", table_name="assessment_question_responses")
    op.drop_table("assessment_question_responses")
    op.drop_constraint("ck_assessment_sessions_v2_state", "assessment_sessions", type_="check")
    op.drop_constraint("ck_assessment_sessions_v2_question_index", "assessment_sessions", type_="check")
    op.drop_column("assessment_sessions", "v2_policy_version")
    op.drop_column("assessment_sessions", "v2_result_json")
    op.drop_column("assessment_sessions", "v2_state")
    op.drop_column("assessment_sessions", "v2_question_index")
