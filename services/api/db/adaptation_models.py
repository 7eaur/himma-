from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from db.models import Base


class AdaptationDecision(Base):
    """Immutable, explainable level decision history for P06.

    Automatic decisions are unique per three-attempt snapshot so refresh/retry cannot
    create duplicate transitions. Manual overrides are independent records and never
    erase the automatic history they supersede operationally.
    """

    __tablename__ = "adaptation_decisions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    decision_source = Column(String(20), nullable=False)  # automatic | manual
    action = Column(String(20), nullable=False)  # promote | stay | support | demote | hold | override
    mastery_score = Column(Numeric(10, 4), nullable=True)
    previous_level = Column(Integer, nullable=False)
    new_level = Column(Integer, nullable=False)
    weakest_skill_id = Column(Integer, ForeignKey("skills.id"), nullable=True)
    valid_attempt_count = Column(Integer, nullable=False, default=0)
    consecutive_low_count = Column(Integer, nullable=False, default=0)
    snapshot_key = Column(String(200), nullable=True)
    explanation = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    manual_reason = Column(String, nullable=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "decision_source",
            "snapshot_key",
            name="uq_adaptation_decision_student_source_snapshot",
        ),
    )
