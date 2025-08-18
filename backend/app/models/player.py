from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Player(SQLModel, table=True):
    __tablename__ = "players"
    
    id: Optional[int] = Field(primary_key=True)
    name: str = Field(max_length=255, nullable=False)
    nickname: str = Field(max_length=100, nullable=False, unique=True, index=True)
    email: Optional[str] = Field(max_length=255, default=None)
    avatar_url: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)