"""Protected endpoints that demonstrate role-based access control."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.models import User, Student
from dependencies import get_db, get_current_user, get_current_student

router = APIRouter(tags=["Protected"])


@router.get("/researcher/dashboard")
def researcher_dashboard(user: User = Depends(get_current_user)):
    """Only accessible to authenticated researchers."""
    return {
        "message": "Welcome to the researcher dashboard",
        "user_id": user.id,
        "username": user.username,
    }


@router.get("/researcher/students")
def list_students(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Researcher-only: list all students."""
    students = db.query(Student).all()
    return [
        {"id": s.id, "name": s.name, "level": s.current_level}
        for s in students
    ]


@router.get("/student/profile")
def student_profile(student: Student = Depends(get_current_student)):
    """Only accessible to authenticated students."""
    return {
        "message": "Welcome to your profile",
        "student_id": student.id,
        "name": student.name,
        "level": student.current_level,
    }
