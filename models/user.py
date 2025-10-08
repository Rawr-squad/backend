from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime

from database.models import AccessStatus


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    firstname: str
    lastname: str
    field: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    disabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdminResponse(BaseModel):
    id : int
    username : str
    created_at : datetime
    update_at : datetime


class AdminCreate(BaseModel):
    username : str
    password : str

# Отдельная схема для логина
class LoginRequest(BaseModel):
    username: str
    password: str


class AccessRequestModel(BaseModel):
    request_data : Dict[str, Any]
    access_period : int
    access_reason : str = None
    secret_id : int
