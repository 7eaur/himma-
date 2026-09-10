"""Revocable authentication session state.

Kept additive to the historical User/Student tables so credential rotation can
invalidate JWTs without rewriting identity/history rows.
"""

from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Column, DateTime, Integer, String, UniqueConstraint, text

from db.models import Base


class AuthSessionState(Base):
    __tablename__ = "auth_session_states"

    id = Column(Integer, primary_key=True, index=True)
    actor_role = Column(String(32), nullable=False)
    actor_id = Column(Integer, nullable=False)
    auth_epoch = Column(Integer, nullable=False, default=0, server_default="0")
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    __table_args__ = (
        UniqueConstraint("actor_role", "actor_id", name="uq_auth_session_state_actor"),
        CheckConstraint("actor_role IN ('researcher','student')", name="ck_auth_session_state_role"),
        CheckConstraint("auth_epoch >= 0", name="ck_auth_session_state_epoch"),
    )
