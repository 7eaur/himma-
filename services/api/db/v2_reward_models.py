"""Append-only effort rewards for a pinned V2 learning journey."""
from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from db.models import Base


class V2RewardGrant(Base):
    __tablename__ = 'v2_reward_grants'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True)
    content_release_id = Column(Integer, ForeignKey('content_releases.id', ondelete='RESTRICT'), nullable=False)
    scope_kind = Column(String(16), nullable=False)
    scope_id = Column(String(32), nullable=False)
    milestone = Column(String(32), nullable=False)
    stars = Column(Integer, nullable=False)
    lesson_session_id = Column(Integer, ForeignKey('lesson_sessions.id', ondelete='SET NULL'), nullable=True)
    policy_version = Column(String(80), nullable=False)
    evidence_json = Column(JSON().with_variant(JSONB, 'postgresql'), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (
        UniqueConstraint('student_id','content_release_id','scope_kind','scope_id','milestone', name='uq_v2_reward_milestone'),
        CheckConstraint("(scope_kind = 'lesson' AND milestone IN ('intro_video','guided_practice','lesson_complete') AND stars = 1) OR (scope_kind = 'level' AND milestone = 'level_complete' AND stars = 0)", name='ck_v2_reward_grant_kind'),
    )
