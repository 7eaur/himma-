"""Bind each V2 audio upload to one workflow container and question.

Revision ID: 0027_v2_audio_upload_binding
Revises: 0026_v2_upload_leases
"""
from alembic import op
import sqlalchemy as sa

revision = "0027_v2_audio_upload_binding"
down_revision = "0026_v2_upload_leases"
branch_labels = None
depends_on = None


def upgrade():
    # Nullable preserves historical rows. New application writes always set the
    # binding, and submission rejects legacy/unbound leases fail-closed.
    op.add_column(
        "v2_audio_upload_leases",
        sa.Column("binding_key", sa.String(255), nullable=True),
    )
    op.create_check_constraint(
        "ck_v2_audio_upload_binding",
        "v2_audio_upload_leases",
        "binding_key IS NULL OR binding_key <> ''",
    )
    op.create_index(
        "ix_v2_audio_upload_student_binding",
        "v2_audio_upload_leases",
        ["student_id", "binding_key"],
    )


def downgrade():
    op.drop_index(
        "ix_v2_audio_upload_student_binding",
        table_name="v2_audio_upload_leases",
    )
    op.drop_constraint(
        "ck_v2_audio_upload_binding",
        "v2_audio_upload_leases",
        type_="check",
    )
    op.drop_column("v2_audio_upload_leases", "binding_key")
