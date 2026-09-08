"""One study-wide admission limit, shared by every supervisor and API worker."""

import os

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from db.models import Student, User


def student_limit() -> int:
    value = int(os.environ.get("HIMMA_MAX_STUDENTS", "50"))
    if value < 1:
        raise ValueError("HIMMA_MAX_STUDENTS must be a positive integer")
    return value


def lock_admissions(db: Session) -> None:
    # All callers lock the same oldest supervisor, never the calling user.
    # A no-op UPDATE also obtains a write lock on SQLite, where FOR UPDATE is
    # ignored. This lock lives until the surrounding admission transaction ends.
    anchor = select(func.min(User.id)).scalar_subquery()
    db.execute(update(User).where(User.id == anchor).values(id=User.id),
               execution_options={"synchronize_session": False})


def capacity(db: Session) -> dict:
    total = db.query(Student).count()  # Inactive students still belong to the study.
    limit = student_limit()
    return {"total": total, "limit": limit, "remaining": max(0, limit - total)}
