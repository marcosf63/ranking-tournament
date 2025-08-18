from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PlayerBase(BaseModel):
    name: str
    nickname: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool = True


class PlayerCreate(PlayerBase):
    pass


class PlayerUpdate(BaseModel):
    name: Optional[str] = None
    nickname: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None


class PlayerResponse(PlayerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlayerListResponse(BaseModel):
    players: list[PlayerResponse]
    total: int
    page: int
    size: int
    pages: int


class PlayerImportItem(BaseModel):
    name: str
    nickname: str
    email: Optional[str] = None


class PlayerImportRequest(BaseModel):
    players: list[PlayerImportItem]
    preview_only: bool = False


class PlayerImportResponse(BaseModel):
    success: int
    errors: list[str]
    previewed: list[PlayerResponse]
    message: str