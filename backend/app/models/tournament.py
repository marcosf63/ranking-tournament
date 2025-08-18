from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Tournament(SQLModel, table=True):
    __tablename__ = "tournaments"
    
    id: Optional[int] = Field(primary_key=True)
    name: str = Field(max_length=255, nullable=False)
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    logo_url: Optional[str] = None
    sort_criteria: str = Field(default="points_desc", max_length=50)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)