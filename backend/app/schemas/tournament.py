from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TournamentBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    logo_url: Optional[str] = None
    sort_criteria: str = "points_desc"


class TournamentCreate(TournamentBase):
    pass


class TournamentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    logo_url: Optional[str] = None
    sort_criteria: Optional[str] = None


class TournamentResponse(TournamentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TournamentListResponse(BaseModel):
    tournaments: list[TournamentResponse]
    total: int
    page: int
    size: int
    pages: int


class TournamentConfig(BaseModel):
    """Configurações específicas do torneio"""
    sort_criteria: str
    allow_negative_scores: bool = False
    max_score_per_player: Optional[float] = None
    min_score_per_player: Optional[float] = None