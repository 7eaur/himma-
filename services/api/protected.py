"""Protected endpoints — researcher dashboard & student profile."""

import secrets
import string
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db.models import User, Student
from dependencies import get_db, get_current_user, get_current_student, get_any_authenticated

router = APIRouter(tags=["Protected"])


# ─── Shared: /me ─────────────────────────────────────────────────────────────
@router.get("/me")
def get_me(auth=Depends(get_any_authenticated)):
    role, entity = auth
    if role == "researcher":
        return {"id": entity.id, "username": entity.username, "full_name": getattr(entity, "username", ""), "role": "researcher"}
    return {"id": entity.id, "full_name": entity.name, "role": "student"}


# ─── Student: /profile (called by student page) ───────────────────────────────
@router.get("/profile")
def student_profile(student: Student = Depends(get_current_student)):
    return {
        "id": student.id,
        "full_name": student.name,
        "access_code": student.access_code,
        "grade": getattr(student, "grade", 1),
        "current_level": student.current_level,
        "status": "active" if student.is_active else "inactive",
    }


# ─── Researcher: list students ────────────────────────────────────────────────
@router.get("/researcher/students")
def list_students(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    students = db.query(Student).all()
    return [
        {
            "id": s.id,
            "full_name": s.name,
            "access_code": s.access_code,
            "grade": getattr(s, "grade", 1),
            "current_level": s.current_level,
            "status": "active" if s.is_active else "inactive",
        }
        for s in students
    ]


# ─── Researcher: create student ───────────────────────────────────────────────
class CreateStudentRequest(BaseModel):
    full_name: str
    grade: int = 1


def _generate_access_code(db: Session) -> str:
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(20):
        code = "".join(secrets.choice(alphabet) for _ in range(3)) + "-" + "".join(secrets.choice(string.digits) for _ in range(4))
        if not db.query(Student).filter(Student.access_code == code).first():
            return code
    raise RuntimeError("Could not generate unique access code")


@router.post("/researcher/students", status_code=status.HTTP_201_CREATED)
def create_student(
    body: CreateStudentRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    code = _generate_access_code(db)
    student = Student(
        access_code=code,
        name=body.full_name,
        current_level=1,
        is_active=True,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return {
        "id": student.id,
        "full_name": student.name,
        "access_code": student.access_code,
        "grade": body.grade,
        "current_level": student.current_level,
        "status": "active",
    }


# ─── Legacy endpoints ─────────────────────────────────────────────────────────
@router.get("/researcher/dashboard")
def researcher_dashboard(user: User = Depends(get_current_user)):
    return {"message": "Welcome to the researcher dashboard", "user_id": user.id, "username": user.username}


@router.get("/student/profile")
def student_profile_legacy(student: Student = Depends(get_current_student)):
    return {"message": "Welcome to your profile", "student_id": student.id, "name": student.name}
