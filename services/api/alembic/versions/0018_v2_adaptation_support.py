"""Add P05 evidence, decisions and bounded support assignments.

Revision ID: 0018_v2_adaptation_support
Revises: 0017_v2_interaction_runtime
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0018_v2_adaptation_support"
down_revision = "0017_v2_interaction_runtime"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_lesson_sessions_stage", "lesson_sessions", type_="check")
    op.create_check_constraint(
        "ck_lesson_sessions_stage",
        "lesson_sessions",
        "stage IN ('intro','video','guided_practice','independent_check','additional_check','support_practice','support_check','waiting_review','supervisor_hold','complete')",
    )
    op.create_table(
        "support_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lesson_session_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("content_release_id", sa.Integer(), nullable=False),
        sa.Column("support_id", sa.String(20), nullable=False),
        sa.Column("focus", sa.String(80), nullable=False),
        sa.Column("target_skill", sa.String(10), nullable=False),
        sa.Column("source_lesson_id", sa.String(20), nullable=False),
        sa.Column("source_level", sa.Integer(), nullable=False),
        sa.Column("support_level", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), server_default="active", nullable=False),
        sa.Column("verification_round", sa.Integer(), server_default="0", nullable=False),
        sa.Column("practice_question_ids", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("check_question_ids", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("return_to", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("policy_version", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("source_level BETWEEN 1 AND 3", name="ck_support_assignments_source_level"),
        sa.CheckConstraint("support_level BETWEEN 1 AND 3", name="ck_support_assignments_support_level"),
        sa.CheckConstraint("mode IN ('additional_check','targeted_support')", name="ck_support_assignments_mode"),
        sa.CheckConstraint("status IN ('active','waiting_review','resolved','escalated')", name="ck_support_assignments_status"),
        sa.CheckConstraint("verification_round BETWEEN 0 AND 1", name="ck_support_assignments_round"),
        sa.ForeignKeyConstraint(["lesson_session_id"], ["lesson_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["content_release_id"], ["content_releases.id"], ondelete="RESTRICT"),
    )
    op.create_index("uq_support_assignments_active_session", "support_assignments", ["lesson_session_id"], unique=True, postgresql_where=sa.text("status IN ('active','waiting_review')"), sqlite_where=sa.text("status IN ('active','waiting_review')"))
    op.create_index("ix_support_assignments_student_status", "support_assignments", ["student_id", "status"])
    op.add_column("lesson_question_responses", sa.Column("support_assignment_id", sa.Integer(), nullable=True))
    op.create_foreign_key("lesson_question_responses_support_assignment_id_fkey", "lesson_question_responses", "support_assignments", ["support_assignment_id"], ["id"], ondelete="SET NULL")

    op.create_table(
        "skill_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("response_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("lesson_session_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("content_release_id", sa.Integer(), nullable=False),
        sa.Column("support_assignment_id", sa.Integer(), nullable=True),
        sa.Column("question_id", sa.String(160), nullable=False),
        sa.Column("source_kind", sa.String(20), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("skill_group", sa.String(10), nullable=False),
        sa.Column("evidence_type", sa.String(80), nullable=False),
        sa.Column("error_focus", sa.String(80), nullable=True),
        sa.Column("support_focus", sa.String(80), nullable=True),
        sa.Column("review_status", sa.String(32), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("hint_used", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("counts_for_mastery", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("policy_version", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("source_kind IN ('lesson','support')", name="ck_skill_evidence_source"),
        sa.CheckConstraint("role IN ('guided_practice','independent_check','support_check')", name="ck_skill_evidence_role"),
        sa.CheckConstraint("review_status IN ('pending_review','graded')", name="ck_skill_evidence_review"),
        sa.ForeignKeyConstraint(["response_id"], ["lesson_question_responses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lesson_session_id"], ["lesson_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["content_release_id"], ["content_releases.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["support_assignment_id"], ["support_assignments.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_skill_evidence_student_skill", "skill_evidence", ["student_id", "skill_group", "created_at"])
    op.create_index("ix_skill_evidence_session_role", "skill_evidence", ["lesson_session_id", "role"])

    op.create_table(
        "adaptation_decisions_v2",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lesson_session_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("content_release_id", sa.Integer(), nullable=False),
        sa.Column("support_assignment_id", sa.Integer(), nullable=True),
        sa.Column("decision_key", sa.String(120), nullable=False),
        sa.Column("decision_kind", sa.String(40), nullable=False),
        sa.Column("reason_code", sa.String(100), nullable=False),
        sa.Column("evidence_ids", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("explanation_json", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("policy_version", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("decision_kind IN ('next_lesson','additional_check','targeted_support','waiting_review','supervisor_hold')", name="ck_adaptation_decisions_v2_kind"),
        sa.ForeignKeyConstraint(["lesson_session_id"], ["lesson_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["content_release_id"], ["content_releases.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["support_assignment_id"], ["support_assignments.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("lesson_session_id", "decision_key", name="uq_adaptation_decisions_v2_key"),
    )
    op.create_index("ix_adaptation_decisions_v2_student_created", "adaptation_decisions_v2", ["student_id", "created_at"])


def downgrade():
    op.drop_index("ix_adaptation_decisions_v2_student_created", table_name="adaptation_decisions_v2")
    op.drop_table("adaptation_decisions_v2")
    op.drop_index("ix_skill_evidence_session_role", table_name="skill_evidence")
    op.drop_index("ix_skill_evidence_student_skill", table_name="skill_evidence")
    op.drop_table("skill_evidence")
    op.drop_constraint("lesson_question_responses_support_assignment_id_fkey", "lesson_question_responses", type_="foreignkey")
    op.drop_column("lesson_question_responses", "support_assignment_id")
    op.drop_index("ix_support_assignments_student_status", table_name="support_assignments")
    op.drop_index("uq_support_assignments_active_session", table_name="support_assignments")
    op.drop_table("support_assignments")
    op.drop_constraint("ck_lesson_sessions_stage", "lesson_sessions", type_="check")
    op.create_check_constraint(
        "ck_lesson_sessions_stage",
        "lesson_sessions",
        "stage IN ('intro','video','guided_practice','independent_check','waiting_review','complete')",
    )
