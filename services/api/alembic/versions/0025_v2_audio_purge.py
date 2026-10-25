"""Durable and auditable deletion of superseded V2 audio objects.

Revision ID: 0025_v2_audio_purge
Revises: 0024_v2_review_claims
"""
from alembic import op
import sqlalchemy as sa

revision = "0025_v2_audio_purge"
down_revision = "0024_v2_review_claims"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "v2_audio_purge_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("storage_key", sa.String(255), nullable=True, unique=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('queued','deleted')", name="ck_v2_audio_purge_status"),
    )
    op.create_index("ix_v2_audio_purge_status_created", "v2_audio_purge_tasks", ["status", "created_at"])


def downgrade():
    op.drop_index("ix_v2_audio_purge_status_created", table_name="v2_audio_purge_tasks")
    op.drop_table("v2_audio_purge_tasks")
