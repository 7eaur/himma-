"""Authentication routes for supervisor and student sessions."""

from datetime import datetime, timedelta, timezone
import os

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from joserfc import jwt
from sqlalchemy.orm import Session

from auth_rate_limit import clear_identifier_rate_limit, enforce_auth_rate_limit
from auth_session_state import current_auth_epoch
from db.models import AuditLog, Student, User
from dependencies import (
    ALGORITHM,
    JWT_KEY,
    get_any_authenticated,
    get_db,
)
from runtime_flags import secure_session_cookie_required
from schemas import MeResponse, ResearcherLogin, StudentLogin

router = APIRouter(prefix="/auth", tags=["Auth"])

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def _set_token_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=secure_session_cookie_required(),
        path="/",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def _create_access_token(*, sub: int, role: str, auth_epoch: int = 0) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"alg": ALGORITHM},
        {
            "sub": str(sub),
            "role": role,
            "aep": int(auth_epoch),
            "iat": now,
            "exp": expire,
        },
        JWT_KEY,
        algorithms=[ALGORITHM],
    )


def _audit(db: Session, *, actor_role: str, actor_id: int, action: str,
           entity_type: str, entity_id: str) -> None:
    db.add(AuditLog(
        actor_role=actor_role,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
    ))
    db.commit()


@router.post("/login")
def supervisor_login(
    creds: ResearcherLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    enforce_auth_rate_limit(request, scope="supervisor-login", identifier=creds.username)
    user = db.query(User).filter(User.username == creds.username).first()
    if (
        not user
        or not user.is_active
        or user.role != "researcher"
        or not verify_password(creds.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="اسم المستخدم أو كلمة المرور غير صحيحة",
        )
    clear_identifier_rate_limit(scope="supervisor-login", identifier=creds.username)
    token = _create_access_token(
        sub=user.id,
        role="researcher",
        auth_epoch=current_auth_epoch(db, actor_role="researcher", actor_id=user.id),
    )
    _set_token_cookie(response, token)
    _audit(db, actor_role="researcher", actor_id=user.id,
           action="LOGIN", entity_type="USER", entity_id=str(user.id))
    return {"message": "تم تسجيل الدخول بنجاح", "role": "researcher"}


@router.post("/student-login")
def student_login(
    creds: StudentLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    enforce_auth_rate_limit(request, scope="student-login", identifier=creds.access_code)
    student = db.query(Student).filter(Student.access_code == creds.access_code).first()
    if not student or not student.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="رمز الدخول غير صحيح، تحقق منه وحاول مرة أخرى",
        )
    clear_identifier_rate_limit(scope="student-login", identifier=creds.access_code)
    token = _create_access_token(
        sub=student.id,
        role="student",
        auth_epoch=current_auth_epoch(db, actor_role="student", actor_id=student.id),
    )
    _set_token_cookie(response, token)
    _audit(db, actor_role="student", actor_id=student.id,
           action="LOGIN", entity_type="STUDENT", entity_id=str(student.id))
    return {"message": "تم تسجيل الدخول بنجاح", "role": "student"}


@router.get("/me", response_model=MeResponse)
def me(auth=Depends(get_any_authenticated)):
    role, entity = auth
    display = entity.username if role == "researcher" else entity.name
    return MeResponse(id=entity.id, role=role, display_name=display)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        "access_token",
        path="/",
        secure=secure_session_cookie_required(),
        httponly=True,
        samesite="lax",
    )
    return {"message": "تم تسجيل الخروج بنجاح"}
