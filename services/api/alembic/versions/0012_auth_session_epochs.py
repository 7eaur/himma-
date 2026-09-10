"""Add revocable authentication session epochs.

Revision ID: 0012_auth_session_epochs
Revises: 0011_active_content_options
"""

from alembic import op
import sqlalchemy as sa

revision = "0012_auth_session_epochs"
down_revision = "0011_active_content_options"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "auth_session_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_role", sa.String(length=32), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("auth_epoch", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("actor_role IN ('researcher','student')", name="ck_auth_session_state_role"),
        sa.CheckConstraint("auth_epoch >= 0", name="ck_auth_session_state_epoch"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("actor_role", "actor_id", name="uq_auth_session_state_actor"),
    )
    op.create_index(op.f("ix_auth_session_states_id"), "auth_session_states", ["id"], unique=False)


def downgrade():
    # Epoch rows are security/session state only; identity and academic history
    # remain in their historical tables and are not deleted by this downgrade.
    op.drop_index(op.f("ix_auth_session_states_id"), table_name="auth_session_states")
    op.drop_table("auth_session_states")
