from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ScoreBase(BaseModel):
    player_id: int
    tournament_id: int
    points: float
    notes: Optional[str] = None


class ScoreCreate(ScoreBase):
    pass


class ScoreUpdate(BaseModel):
    points: Optional[float] = None
    notes: Optional[str] = None


class ScoreResponse(ScoreBase):
    id: int
    admin_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ScoreWithDetails(ScoreResponse):
    player_name: str
    player_nickname: str
    tournament_name: str
    admin_name: str


class ScoreListResponse(BaseModel):
    scores: list[ScoreResponse]
    total: int
    page: int
    size: int
    pages: int


class ScoreImportItem(BaseModel):
    player_id: int
    tournament_id: int
    points: float
    notes: Optional[str] = None


class ScoreImportRequest(BaseModel):
    scores: list[ScoreImportItem]
    preview_only: bool = False


class ScoreImportResponse(BaseModel):
    success: int
    errors: list[str]
    previewed: list[ScoreResponse]
    message: str