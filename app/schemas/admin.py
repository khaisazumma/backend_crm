from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr


class AdminRole(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    SALES = "SALES"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: "AdminOut"


class AdminCreate(BaseModel):
    email: EmailStr
    password: str
    role: AdminRole = AdminRole.ADMIN


class AdminOut(BaseModel):
    id: int
    email: EmailStr
    role: AdminRole
    is_active: bool
    created_at: datetime
