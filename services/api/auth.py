from datetime import datetime, timedelta, timezone
import os
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt
from db.models import User, AuditLog
from db.database import SessionLocal
from schemas import UserLogin, UserResponse
from dependencies import get_db

router = APIRouter(prefix="/auth", tags=["Auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "dev_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, API_SECRET_KEY, algorithm=ALGORITHM)

@router.post("/login")
def login(user_credentials: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_credentials.username).first()
    
    if not user or not pwd_context.verify(user_credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    
    # Set Secure HttpOnly SameSite cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=os.getenv("ENV") == "production" # Secure true in production
    )
    
    # Audit log
    audit = AuditLog(user_id=user.id, action="LOGIN", entity_type="USER", entity_id=str(user.id))
    db.add(audit)
    db.commit()
    
    return {"message": "Logged in successfully"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}
