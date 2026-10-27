"""Keep historical V1 evidence readable without opening parallel learner writes for V2 students."""

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from db.learning_models import StudentJourney
from db.models import Student
from dependencies import get_current_student, get_db


def require_legacy_student(db: Session, student: Student) -> None:
    if db.query(StudentJourney.student_id).filter(StudentJourney.student_id == student.id).first():
        raise HTTPException(status_code=409, detail="هذا الحساب يتابع رحلته في الإصدار الثاني")


def legacy_student_only(
    db: Session = Depends(get_db), student: Student = Depends(get_current_student),
) -> None:
    require_legacy_student(db, student)
