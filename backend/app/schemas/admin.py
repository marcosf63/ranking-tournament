from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class AdminBase(BaseModel):
    name: str
    email: EmailStr
    permission_level: str = "moderator"
    is_active: bool = True


class AdminCreate(AdminBase):
    password: str


class AdminUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    permission_level: Optional[str] = None
    is_active: Optional[bool] = None


class AdminPasswordUpdate(BaseModel):
    current_password: str
    new_password: str


class AdminResponse(AdminBase):
    id: int
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AdminListResponse(BaseModel):
    admins: list[AdminResponse]
    total: int
    page: int
    size: int
    pages: int


class AdminStats(BaseModel):
    total_admins: int
    active_admins: int
    super_admins: int
    moderators: int
    recent_logins: int