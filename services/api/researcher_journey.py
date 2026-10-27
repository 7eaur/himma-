"""Supervisor projection of the canonical student journey.

This router intentionally delegates all academic state to ``journey.py``.
It exists only to expose the same projection to the authenticated supervisor so
Admin UI never reconstructs level completion from ``current_level``.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.models import Student, User
from dependencies import get_current_user, get_db
from journey import build_journey_summary

router = APIRouter(prefix="/researcher/students", tags=["Researcher Journey"])


@router.get("/{student_id}/journey")
def researcher_student_journey(
    student_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")
    return build_journey_summary(db, student)
