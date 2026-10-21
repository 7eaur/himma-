"""Add resumable P03 lesson video progress and idempotent events.

Revision ID: 0016_v2_lesson_runtime
Revises: 0015_v2_learning_foundation
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0016_v2_lesson_runtime"
down_revision = "0015_v2_learning_foundation"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("lesson_sessions", sa.Column("intro_seen", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("lesson_sessions", sa.Column("video_position_seconds", sa.Float(), server_default="0", nullable=False))
    op.add_column("lesson_sessions", sa.Column("video_duration_seconds", sa.Float(), nullable=True))
    op.add_column("lesson_sessions", sa.Column("video_completed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "lesson_progress_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lesson_session_id", sa.Integer(), nullable=False),
        sa.Column("event_key", sa.String(100), nullable=False),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("payload_json", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("event_type IN ('intro_complete','video_progress','video_ended')", name="ck_lesson_progress_events_type"),
        sa.ForeignKeyConstraint(["lesson_session_id"], ["lesson_sessions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("lesson_session_id", "event_key", name="uq_lesson_progress_event_key"),
    )
    op.create_index("ix_lesson_progress_events_session_created", "lesson_progress_events", ["lesson_session_id", "created_at"])


def downgrade():
    op.drop_index("ix_lesson_progress_events_session_created", table_name="lesson_progress_events")
    op.drop_table("lesson_progress_events")
    for column in ("video_completed_at", "video_duration_seconds", "video_position_seconds", "intro_seen"):
        op.drop_column("lesson_sessions", column)
