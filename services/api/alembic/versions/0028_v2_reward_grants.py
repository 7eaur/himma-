"""Add isolated append-only V2 effort reward ledger; no V1 backfill.
Revision ID: 0028_v2_reward_grants
Revises: 0027_v2_audio_upload_binding
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = '0028_v2_reward_grants'
down_revision = '0027_v2_audio_upload_binding'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('v2_reward_grants',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('student_id',sa.Integer(),sa.ForeignKey('students.id',ondelete='CASCADE'),nullable=False),
        sa.Column('content_release_id',sa.Integer(),sa.ForeignKey('content_releases.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('scope_kind',sa.String(16),nullable=False),sa.Column('scope_id',sa.String(32),nullable=False),
        sa.Column('milestone',sa.String(32),nullable=False),sa.Column('stars',sa.Integer(),nullable=False),
        sa.Column('lesson_session_id',sa.Integer(),sa.ForeignKey('lesson_sessions.id',ondelete='SET NULL'),nullable=True),
        sa.Column('policy_version',sa.String(80),nullable=False),
        sa.Column('evidence_json',sa.JSON().with_variant(postgresql.JSONB,'postgresql'),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),
        sa.UniqueConstraint('student_id','content_release_id','scope_kind','scope_id','milestone',name='uq_v2_reward_milestone'),
        sa.CheckConstraint("(scope_kind = 'lesson' AND milestone IN ('intro_video','guided_practice','lesson_complete') AND stars = 1) OR (scope_kind = 'level' AND milestone = 'level_complete' AND stars = 0)",name='ck_v2_reward_grant_kind'),
    )
    op.create_index('ix_v2_reward_grants_student_id','v2_reward_grants',['student_id'])


def downgrade():
    op.drop_index('ix_v2_reward_grants_student_id',table_name='v2_reward_grants')
    op.drop_table('v2_reward_grants')
