"""Allow audited automatic V2 placement after final human-reviewed audio.

Revision ID: 0029_v2_system_placement
Revises: 0028_v2_reward_grants
Only relaxes the actor FK's NOT NULL constraint; no student data changes.
"""
from alembic import op
import sqlalchemy as sa

revision = "0029_v2_system_placement"
down_revision = "0028_v2_reward_grants"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("placement_decisions_v2") as batch:
        batch.alter_column("decided_by", existing_type=sa.Integer(), nullable=True)


def downgrade():
    # Refuse destructive "repair" of system-owned academic decisions.
    connection = op.get_bind()
    missing = connection.execute(
        sa.text("SELECT count(*) FROM placement_decisions_v2 WHERE decided_by IS NULL")
    ).scalar()
    if missing:
        raise RuntimeError(
            "System placement rows exist: preserve them and use a compatible "
            "application rollback. Requiring a human actor would corrupt audit data."
        )
    with op.batch_alter_table("placement_decisions_v2") as batch:
        batch.alter_column("decided_by", existing_type=sa.Integer(), nullable=False)
