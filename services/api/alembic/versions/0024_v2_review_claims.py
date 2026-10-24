"""Short, serialized supervisor review claims for V2 open evidence.

Revision ID: 0024_v2_review_claims
Revises: 0023_v2_review_retry
"""
from alembic import op
import sqlalchemy as sa

revision = "0024_v2_review_claims"
down_revision = "0023_v2_review_retry"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "v2_review_claims",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lesson_response_id", sa.Integer(), sa.ForeignKey("lesson_question_responses.id", ondelete="CASCADE"), nullable=True, unique=True),
        sa.Column("assessment_response_id", sa.Integer(), sa.ForeignKey("assessment_question_responses.id", ondelete="CASCADE"), nullable=True, unique=True),
        sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(CASE WHEN lesson_response_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN assessment_response_id IS NOT NULL THEN 1 ELSE 0 END) = 1",
            name="ck_v2_review_claim_exactly_one_owner",
        ),
    )
    op.create_index("ix_v2_review_claim_reviewer", "v2_review_claims", ["reviewer_id", "expires_at"])


def downgrade():
    op.drop_index("ix_v2_review_claim_reviewer", table_name="v2_review_claims")
    op.drop_table("v2_review_claims")
