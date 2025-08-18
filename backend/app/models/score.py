from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Score(SQLModel, table=True):
    __tablename__ = "scores"
    
    id: Optional[int] = Field(primary_key=True)
    player_id: int = Field(foreign_key="players.id", nullable=False, index=True)
    tournament_id: int = Field(foreign_key="tournaments.id", nullable=False, index=True)
    points: float = Field(nullable=False)
    notes: Optional[str] = None
    admin_id: int = Field(foreign_key="admins.id", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)