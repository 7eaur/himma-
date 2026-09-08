"""Retain retired option identities for historical student responses."""
from alembic import op
import sqlalchemy as sa

revision = "0011_active_content_options"
down_revision = "0010_researcher_notifications"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("content_options", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade():
    # Old application versions expose every row. Never silently reactivate
    # retired answers or delete the evidence to make a downgrade succeed.
    retired = op.get_bind().execute(sa.text("SELECT count(*) FROM content_options WHERE is_active = false")).scalar_one()
    if retired:
        raise RuntimeError("Retired options exist; restore a verified pre-migration backup with matching application code instead of dropping lifecycle state.")
    op.drop_column("content_options", "is_active")
