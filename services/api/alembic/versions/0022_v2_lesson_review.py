"""Append-only V2 lesson review action log.

Revision ID: 0022_v2_lesson_review
Revises: 0021_private_bank_snapshot
"""
from alembic import op
import sqlalchemy as sa

revision = "0022_v2_lesson_review"
down_revision = "0021_private_bank_snapshot"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "v2_lesson_review_actions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lesson_response_id", sa.Integer(), sa.ForeignKey("lesson_question_responses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("note", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("action IN ('graded')", name="ck_v2_lesson_review_action_kind"),
    )
    op.create_index("ix_v2_lesson_review_actions_response", "v2_lesson_review_actions", ["lesson_response_id", "created_at"])


def downgrade():
    op.drop_index("ix_v2_lesson_review_actions_response", table_name="v2_lesson_review_actions")
    op.drop_table("v2_lesson_review_actions")
