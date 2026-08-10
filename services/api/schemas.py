from pydantic import BaseModel
from typing import Optional


class ResearcherLogin(BaseModel):
    username: str
    password: str


class StudentLogin(BaseModel):
    access_code: str


class UserResponse(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        from_attributes = True


class StudentResponse(BaseModel):
    id: int
    name: str
    access_code: str
    current_level: int

    class Config:
        from_attributes = True


class MeResponse(BaseModel):
    """Returned by /auth/me — works for both roles."""
    id: int
    role: str
    display_name: str
