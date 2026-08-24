"""Protected endpoints — researcher dashboard and student lifecycle."""

import json
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.models import AssessmentSession, AuditLog, Student, User
from dependencies import get_db, get_current_user, get_current_student, get_any_authenticated
import schemas

router = APIRouter(tags=["Protected"])


# ─── Shared: /me ─────────────────────────────────────────────────────────────
@router.get("/me")
def get_me(auth=Depends(get_any_authenticated)):
    role, entity = auth
    if role == "researcher":
        return {"id": entity.id, "username": entity.username, "full_name": getattr(entity, "username", ""), "role": "researcher"}
    return {"id": entity.id, "full_name": entity.name, "role": "student"}


# ─── Student: /profile (called by student page) ───────────────────────────────
def _completed_session(db: Session, student_id: int, session_type: str) -> bool:
    return db.query(AssessmentSession.id).filter(
        AssessmentSession.student_id == student_id,
        AssessmentSession.session_type == session_type,
        AssessmentSession.status == "completed",
    ).first() is not None


def _student_payload(db: Session, student: Student) -> dict:
    pretest_completed = _completed_session(db, student.id, "pretest")
    posttest_completed = _completed_session(db, student.id, "posttest")
    return {
        "id": student.id,
        "full_name": student.name,
        "access_code": student.access_code,
        "grade_level": student.grade_level,
        "current_level": student.current_level,
        "status": "active" if student.is_active else "inactive",
        "posttest_enabled": student.posttest_enabled,
        "posttest_eligible": pretest_completed and not posttest_completed,
        "created_at": student.created_at,
    }


@router.get("/profile", response_model=schemas.StudentProfileResponse)
def student_profile(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    active_session = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student.id,
        AssessmentSession.status == "in_progress",
    ).order_by(AssessmentSession.id.desc()).first()
    pretest_completed = _completed_session(db, student.id, "pretest")
    posttest_completed = _completed_session(db, student.id, "posttest")
    if active_session:
        next_action = "resume"
    elif not pretest_completed:
        next_action = "pretest"
    elif posttest_completed:
        next_action = "completed"
    elif student.posttest_enabled:
        next_action = "posttest"
    else:
        next_action = "learning"
    return {
        "id": student.id,
        "full_name": student.name,
        "access_code": student.access_code,
        "grade_level": student.grade_level,
        "current_level": student.current_level,
        "status": "active" if student.is_active else "inactive",
        "posttest_enabled": student.posttest_enabled,
        "next_action": next_action,
        "active_session": active_session,
    }


# ─── Researcher: list students ────────────────────────────────────────────────
@router.get("/researcher/students", response_model=list[schemas.StudentResponse])
def list_students(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    students = db.query(Student).order_by(Student.created_at, Student.id).all()
    return [_student_payload(db, student) for student in students]


@router.get("/researcher/students/{student_id}", response_model=schemas.StudentResponse)
def get_student(
    student_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return _student_payload(db, student)


# ─── Researcher: create student ───────────────────────────────────────────────
def _generate_access_code(db: Session) -> str:
    letters = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    digits = "23456789"
    for _ in range(20):
        code = "".join(secrets.choice(letters) for _ in range(4)) + "-" + "".join(
            secrets.choice(digits) for _ in range(4)
        )
        if not db.query(Student).filter(Student.access_code == code).first():
            return code
    raise RuntimeError("Could not generate unique access code")


@router.post(
    "/researcher/students",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.StudentResponse,
)
def create_student(
    body: schemas.StudentCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Serializing on the single researcher row keeps the 15-student cap exact
    # on PostgreSQL even when two creates arrive at the same time.
    db.query(User).filter(User.id == user.id).with_for_update().one()
    if db.query(Student).count() >= 15:
        raise HTTPException(status_code=409, detail="The study is limited to 15 students")

    for _ in range(5):
        student = Student(
            access_code=_generate_access_code(db),
            name=body.full_name,
            grade_level=body.grade_level,
            current_level=1,
            is_active=True,
        )
        try:
            with db.begin_nested():
                db.add(student)
                db.flush()
        except IntegrityError:
            continue

        db.add(AuditLog(
            actor_role="researcher",
            actor_id=user.id,
            action="student.create",
            entity_type="student",
            entity_id=str(student.id),
            details=json.dumps({"grade_level": 3}, sort_keys=True),
        ))
        db.commit()
        db.refresh(student)
        return _student_payload(db, student)

    raise HTTPException(status_code=503, detail="Could not allocate a student access code")


@router.post(
    "/researcher/students/{student_id}/posttest-access",
    response_model=schemas.StudentResponse,
)
def set_posttest_access(
    student_id: int,
    body: schemas.StudentPosttestAccessRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(Student.id == student_id).with_for_update().first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    pretest_completed = _completed_session(db, student.id, "pretest")
    posttest_completed = _completed_session(db, student.id, "posttest")
    if posttest_completed:
        raise HTTPException(status_code=409, detail="The posttest is already completed")
    posttest_active = db.query(AssessmentSession.id).filter(
        AssessmentSession.student_id == student.id,
        AssessmentSession.session_type == "posttest",
        AssessmentSession.status == "in_progress",
    ).first()
    if posttest_active:
        raise HTTPException(status_code=409, detail="The posttest is currently in progress")
    if body.enabled and not pretest_completed:
        raise HTTPException(status_code=409, detail="Complete the pretest before enabling the posttest")

    student.posttest_enabled = body.enabled
    student.posttest_enabled_at = datetime.now(timezone.utc) if body.enabled else None
    student.posttest_enabled_by = user.id if body.enabled else None
    db.add(AuditLog(
        actor_role="researcher",
        actor_id=user.id,
        action="student.posttest_access.update",
        entity_type="student",
        entity_id=str(student.id),
        details=json.dumps({"enabled": body.enabled}, sort_keys=True),
    ))
    db.commit()
    db.refresh(student)
    return _student_payload(db, student)


# ─── Legacy endpoints ─────────────────────────────────────────────────────────
@router.get("/researcher/dashboard")
def researcher_dashboard(user: User = Depends(get_current_user)):
    return {"message": "Welcome to the researcher dashboard", "user_id": user.id, "username": user.username}


@router.get("/student/profile")
def student_profile_legacy(student: Student = Depends(get_current_student)):
    return {"message": "Welcome to your profile", "student_id": student.id, "name": student.name}
