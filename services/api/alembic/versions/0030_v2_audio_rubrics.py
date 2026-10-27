"""Isolate V2 human reading observations without touching V1 audio_reviews.

Revision ID: 0030_v2_audio_rubrics
Revises: 0029_v2_system_placement
This additive migration preserves all student submissions and audio files.
"""
from alembic import op
import sqlalchemy as sa

revision = "0030_v2_audio_rubrics"
down_revision = "0029_v2_system_placement"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "v2_audio_rubrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("audio_submission_id", sa.Integer(), sa.ForeignKey("audio_submissions.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("target_units", sa.Integer(), nullable=False),
        sa.Column("deletions", sa.Integer(), nullable=False),
        sa.Column("substitutions", sa.Integer(), nullable=False),
        sa.Column("insertions", sa.Integer(), nullable=False),
        sa.Column("rubric_score", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("pronunciation_notes", sa.String(), nullable=True),
        sa.Column("fluency_notes", sa.String(), nullable=True),
        sa.Column("policy_version", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("target_units BETWEEN 1 AND 1000", name="ck_v2_audio_rubric_target"),
        sa.CheckConstraint("deletions >= 0 AND substitutions >= 0 AND insertions >= 0", name="ck_v2_audio_rubric_errors"),
        sa.CheckConstraint("deletions + substitutions <= target_units", name="ck_v2_audio_rubric_exclusive_units"),
        sa.CheckConstraint("rubric_score BETWEEN 0 AND 1", name="ck_v2_audio_rubric_score"),
    )
    op.create_index("ix_v2_audio_rubrics_reviewer", "v2_audio_rubrics", ["reviewer_id", "created_at"])


def downgrade():
    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT count(*) FROM v2_audio_rubrics")).scalar()
    if rows:
        raise RuntimeError("Cannot discard child reading grades: use a compatible deployment rollback preserving V2 evidence")
    op.drop_index("ix_v2_audio_rubrics_reviewer", table_name="v2_audio_rubrics")
    op.drop_table("v2_audio_rubrics")
