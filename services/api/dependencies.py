"""Dependency injection for FastAPI endpoints."""

import os
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from db.database import SessionLocal
from db.models import User, Student

API_SECRET_KEY = os.getenv("API_SECRET_KEY")
if not API_SECRET_KEY:
    raise RuntimeError(
        "API_SECRET_KEY environment variable is required. "
        "Set it before starting the application."
    )
ALGORITHM = "HS256"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _decode_token(request: Request) -> dict:
    """Extract and decode the JWT from the access_token cookie."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        payload = jwt.decode(token, API_SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    return payload


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Resolve the authenticated *researcher* from cookie JWT."""
    payload = _decode_token(request)
    role = payload.get("role")
    if role != "researcher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Researcher access required",
        )
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


def get_current_student(request: Request, db: Session = Depends(get_db)) -> Student:
    """Resolve the authenticated *student* from cookie JWT."""
    payload = _decode_token(request)
    role = payload.get("role")
    if role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required",
        )
    student_id = payload.get("sub")
    student = db.query(Student).filter(Student.id == int(student_id)).first()
    if student is None or not student.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Student not found",
        )
    return student


def get_any_authenticated(request: Request, db: Session = Depends(get_db)):
    """Return (role, entity) for any valid session — used by /auth/me."""
    payload = _decode_token(request)
    role = payload.get("role")
    entity_id = payload.get("sub")
    if role == "researcher":
        entity = db.query(User).filter(User.id == int(entity_id)).first()
    elif role == "student":
        entity = db.query(Student).filter(Student.id == int(entity_id)).first()
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unknown role")
    if entity is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not found")
    return role, entity
