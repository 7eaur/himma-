"""Shared, SQL-backed V2 retry state. No direct student/public DTO is returned."""
from __future__ import annotations

from sqlalchemy.orm import Session
from db.learning_models import V2ReviewRetryTask

ACTIVE = ("requested", "submitted")


def active_retry(db: Session, *, lesson_response_id: int | None = None, assessment_response_id: int | None = None) -> V2ReviewRetryTask | None:
    if (lesson_response_id is None) == (assessment_response_id is None):
        raise ValueError("Specify exactly one review response owner")
    query = db.query(V2ReviewRetryTask).filter(V2ReviewRetryTask.status.in_(ACTIVE))
    if lesson_response_id is not None:
        query = query.filter(V2ReviewRetryTask.lesson_response_id == lesson_response_id)
    else:
        query = query.filter(V2ReviewRetryTask.assessment_response_id == assessment_response_id)
    return query.order_by(V2ReviewRetryTask.id.desc()).first()
