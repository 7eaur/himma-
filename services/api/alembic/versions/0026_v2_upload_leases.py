"""Track unsubmitted V2 audio so abandoned uploads can be purged after a grace period.

Revision ID: 0026_v2_upload_leases
Revises: 0025_v2_audio_purge
"""
from alembic import op
import sqlalchemy as sa

revision = "0026_v2_upload_leases"
down_revision = "0025_v2_audio_purge"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "v2_audio_upload_leases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("storage_key", sa.String(255), nullable=True, unique=True),
        sa.Column("state", sa.String(20), nullable=False, server_default="temporary"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("state IN ('temporary','submitted','purged')", name="ck_v2_audio_upload_state"),
    )
    op.create_index("ix_v2_audio_upload_state_created", "v2_audio_upload_leases", ["state", "created_at"])


def downgrade():
    op.drop_index("ix_v2_audio_upload_state_created", table_name="v2_audio_upload_leases")
    op.drop_table("v2_audio_upload_leases")
