from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    role: str = "qa_staff"
    squad_id: Optional[int] = None
    squad_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


# =====================================================
# ADMIN USER MANAGEMENT SCHEMAS
# =====================================================

class UserUpdate(BaseModel):
    """Admin update payload — all fields optional."""
    role: Optional[str] = Field(None, pattern="^(admin|kabag|qa_lead|qa_staff)$")
    is_active: Optional[bool] = None
    squad_id: Optional[int] = None
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserListItem(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    role: str
    squad_id: Optional[int] = None
    squad_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    users: List[UserListItem]
    total: int
    skip: int
    limit: int


# =====================================================
# SQUAD SCHEMAS
# =====================================================

class SquadCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class SquadUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class SquadResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    member_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class SquadListResponse(BaseModel):
    squads: List[SquadResponse]
    total: int


class SquadMemberItem(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class SquadDetailResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    members: List[SquadMemberItem]
