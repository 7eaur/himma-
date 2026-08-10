from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    class Config:
        from_attributes = True

class StudentCreate(BaseModel):
    name: str

class StudentResponse(BaseModel):
    id: int
    name: str
    access_code: str
    current_level: int
    class Config:
        from_attributes = True
