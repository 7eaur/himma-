"""Separate private assessment answer snapshots from release metadata.

Revision ID: 0021_private_content_bank_snapshot
Revises: 0020_v2_official_attempt_guard
"""
from datetime import datetime, timezone
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0021_private_content_bank_snapshot"
down_revision = "0020_v2_official_attempt_guard"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "private_content_bank_snapshots",
        sa.Column("content_release_id", sa.Integer(), sa.ForeignKey("content_releases.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("payload_json", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        conn.execute(sa.text("""
            INSERT INTO private_content_bank_snapshots (content_release_id, checksum, payload_json, created_at)
            SELECT id, checksum, manifest_json::jsonb->'bank_snapshot', CURRENT_TIMESTAMP
            FROM content_releases
            WHERE manifest_json::jsonb ? 'bank_snapshot' AND checksum IS NOT NULL
            ON CONFLICT (content_release_id) DO NOTHING
        """))
        conn.execute(sa.text("""
            UPDATE content_releases
            SET manifest_json = manifest_json::jsonb - 'bank_snapshot'
            WHERE manifest_json::jsonb ? 'bank_snapshot'
        """))
    else:
        import json
        for item in conn.execute(sa.text("SELECT id, checksum, manifest_json FROM content_releases")).fetchall():
            manifest = item.manifest_json
            if isinstance(manifest, str):
                manifest = json.loads(manifest)
            if not isinstance(manifest, dict) or "bank_snapshot" not in manifest:
                continue
            payload = manifest.pop("bank_snapshot")
            conn.execute(sa.text(
                "INSERT INTO private_content_bank_snapshots (content_release_id, checksum, payload_json, created_at) "
                "VALUES (:id, :checksum, :payload, :created)"
            ), {"id": item.id, "checksum": item.checksum, "payload": json.dumps(payload, ensure_ascii=False),
                "created": datetime.now(timezone.utc)})
            conn.execute(sa.text("UPDATE content_releases SET manifest_json = :manifest WHERE id = :id"),
                {"manifest": json.dumps(manifest, ensure_ascii=False), "id": item.id})


def downgrade():
    raise RuntimeError("Unsafe downgrade would destroy pinned private answer snapshots")
