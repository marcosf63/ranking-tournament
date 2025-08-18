from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Admin(SQLModel, table=True):
    __tablename__ = "admins"
    
    id: Optional[int] = Field(primary_key=True)
    name: str = Field(max_length=255, nullable=False)
    email: str = Field(max_length=255, nullable=False, unique=True, index=True)
    password_hash: str = Field(nullable=False)
    permission_level: str = Field(default="moderator", max_length=20)
    is_active: bool = Field(default=True)
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)