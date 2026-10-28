"""Retire V2 free-writing storage, failing closed if historical evidence remains.

Revision ID: 0031_v2_reading_only
Revises: 0030_v2_audio_rubrics
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0031_v2_reading_only"
down_revision = "0030_v2_audio_rubrics"
branch_labels = None
depends_on = None


def _require_empty(connection, table: str) -> None:
    if table not in {"lesson_question_drafts", "assessment_question_drafts"}:
        raise RuntimeError("Unexpected cleanup table")
    count = connection.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
    if count:
        raise RuntimeError(
            f"V2 reading-only migration refused: {table} has {count} draft row(s); "
            "inspect the owners and use authorized account erasure, never silently discard evidence"
        )


def upgrade():
    connection = op.get_bind()
    _require_empty(connection, "lesson_question_drafts")
    _require_empty(connection, "assessment_question_drafts")
    retired = connection.execute(sa.text(
        "SELECT COUNT(*) FROM v2_review_retry_tasks WHERE request_kind <> 'rerecord'"
    )).scalar_one()
    if retired:
        raise RuntimeError(
            f"V2 reading-only migration refused: {retired} legacy rewrite task(s) still exist"
        )
    op.drop_table("lesson_question_drafts")
    op.drop_table("assessment_question_drafts")
    op.drop_constraint("ck_v2_retry_kind", "v2_review_retry_tasks", type_="check")
    op.create_check_constraint(
        "ck_v2_retry_kind", "v2_review_retry_tasks", "request_kind = 'rerecord'"
    )


def downgrade():
    # Empty former tables can be reconstructed; upgrade never discards rows.
    op.drop_constraint("ck_v2_retry_kind", "v2_review_retry_tasks", type_="check")
    op.create_check_constraint(
        "ck_v2_retry_kind", "v2_review_retry_tasks",
        "request_kind IN ('rerecord','rewrite')",
    )
    op.create_table(
        "lesson_question_drafts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lesson_session_id", sa.Integer(), sa.ForeignKey("lesson_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.String(160), nullable=False),
        sa.Column("draft_json", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("version >= 1", name="ck_lesson_question_drafts_version"),
        sa.UniqueConstraint("lesson_session_id", "question_id", name="uq_lesson_question_draft"),
    )
    op.create_table(
        "assessment_question_drafts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("assessment_session_id", sa.Integer(), sa.ForeignKey("assessment_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.String(160), nullable=False),
        sa.Column("draft_json", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("version >= 1", name="ck_assessment_question_draft_version"),
        sa.UniqueConstraint("assessment_session_id", "question_id", name="uq_assessment_question_draft"),
    )
