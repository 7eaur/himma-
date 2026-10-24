"""Enforce one official pre/post attempt per student across V1 and V2.

Revision ID: 0020_v2_official_attempt_guard
Revises: 0019_v2_assessment_runtime
"""
from alembic import op
import sqlalchemy as sa

revision = "0020_v2_official_attempt_guard"
down_revision = "0019_v2_assessment_runtime"
branch_labels = None
depends_on = None


def upgrade():
    # Historical duplicate flags must be normalized before the unique index.
    # Preserve every attempt, its score, and its supersedes chain.
    op.execute(sa.text("""
        UPDATE assessment_sessions AS s
        SET official_for_reporting = FALSE
        WHERE s.id IN (
          SELECT id FROM (
            SELECT id, ROW_NUMBER() OVER (
                PARTITION BY student_id, session_type
                ORDER BY completed_at DESC NULLS LAST, id DESC
            ) AS rank_no
            FROM assessment_sessions
            WHERE official_for_reporting IS TRUE
              AND status = 'completed'
              AND session_type IN ('pretest', 'posttest')
          ) ranked WHERE rank_no > 1
        )
    """))
    op.create_index(
        "uq_assessment_sessions_official_student_kind",
        "assessment_sessions", ["student_id", "session_type"], unique=True,
        postgresql_where=sa.text("official_for_reporting IS TRUE AND status = 'completed' AND session_type IN ('pretest','posttest')"),
        sqlite_where=sa.text("official_for_reporting IS TRUE AND status = 'completed' AND session_type IN ('pretest','posttest')"),
    )


def downgrade():
    op.drop_index("uq_assessment_sessions_official_student_kind", table_name="assessment_sessions")
