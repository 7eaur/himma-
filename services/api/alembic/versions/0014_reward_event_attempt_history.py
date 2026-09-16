"""Preserve reward history when operational attempts are deleted.

Revision ID: 0014_reward_event_attempt_history
Revises: 0013_speech_job_leases
"""

from alembic import op


revision = "0014_reward_event_attempt_history"
down_revision = "0013_speech_job_leases"
branch_labels = None
depends_on = None


CONSTRAINT = "reward_events_attempt_id_fkey"


def upgrade():
    op.drop_constraint(CONSTRAINT, "reward_events", type_="foreignkey")
    op.create_foreign_key(
        CONSTRAINT,
        "reward_events",
        "attempts",
        ["attempt_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint(CONSTRAINT, "reward_events", type_="foreignkey")
    op.create_foreign_key(
        CONSTRAINT,
        "reward_events",
        "attempts",
        ["attempt_id"],
        ["id"],
        ondelete="CASCADE",
    )
