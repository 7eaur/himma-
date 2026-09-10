"""Add durable claim leases to speech-analysis jobs.

Revision ID: 0013_speech_job_leases
Revises: 0012_auth_session_epochs
"""

from alembic import op
import sqlalchemy as sa

revision = "0013_speech_job_leases"
down_revision = "0012_auth_session_epochs"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("speech_analysis_jobs", sa.Column("lease_owner", sa.String(length=160), nullable=True))
    op.add_column("speech_analysis_jobs", sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.drop_index("ix_speech_jobs_claim", table_name="speech_analysis_jobs")
    op.create_index(
        "ix_speech_jobs_claim",
        "speech_analysis_jobs",
        ["status", "next_attempt_at", "lease_expires_at", "created_at"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_speech_jobs_claim", table_name="speech_analysis_jobs")
    op.create_index(
        "ix_speech_jobs_claim",
        "speech_analysis_jobs",
        ["status", "next_attempt_at", "created_at"],
        unique=False,
    )
    op.drop_column("speech_analysis_jobs", "lease_expires_at")
    op.drop_column("speech_analysis_jobs", "lease_owner")
