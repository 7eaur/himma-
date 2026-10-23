"""Add P04 drafts and reuse audio submissions for V2 lesson responses.

Revision ID: 0017_v2_interaction_runtime
Revises: 0016_v2_lesson_runtime
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0017_v2_interaction_runtime"
down_revision = "0016_v2_lesson_runtime"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("audio_submissions", "response_id", existing_type=sa.Integer(), nullable=True)
    op.add_column("audio_submissions", sa.Column("lesson_response_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "audio_submissions_lesson_response_id_fkey",
        "audio_submissions",
        "lesson_question_responses",
        ["lesson_response_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_check_constraint(
        "ck_audio_submissions_one_response_owner",
        "audio_submissions",
        "(response_id IS NOT NULL AND lesson_response_id IS NULL) OR "
        "(response_id IS NULL AND lesson_response_id IS NOT NULL)",
    )
    op.create_table(
        "lesson_question_drafts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lesson_session_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.String(160), nullable=False),
        sa.Column("draft_json", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("version >= 1", name="ck_lesson_question_drafts_version"),
        sa.ForeignKeyConstraint(["lesson_session_id"], ["lesson_sessions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("lesson_session_id", "question_id", name="uq_lesson_question_draft"),
    )


def downgrade():
    op.drop_table("lesson_question_drafts")
    op.drop_constraint("ck_audio_submissions_one_response_owner", "audio_submissions", type_="check")
    op.drop_constraint("audio_submissions_lesson_response_id_fkey", "audio_submissions", type_="foreignkey")
    op.drop_column("audio_submissions", "lesson_response_id")
    op.alter_column("audio_submissions", "response_id", existing_type=sa.Integer(), nullable=False)
