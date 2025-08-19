from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PlayerSearchResult(BaseModel):
    id: int
    name: str
    nickname: str
    avatar_url: Optional[str] = None
    total_tournaments: int
    total_points: float
    position: int


class TournamentSearchResult(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    participants_count: int
    is_active: bool


class SearchResult(BaseModel):
    type: str  # "player" ou "tournament"
    id: int
    name: str
    description: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    players: List[PlayerSearchResult]
    tournaments: List[TournamentSearchResult]
    total_results: int


class SearchSuggestion(BaseModel):
    text: str
    type: str  # "player" ou "tournament"
    field: str  # "name", "nickname", etc.


class SuggestionsResponse(BaseModel):
    query: str
    suggestions: List[SearchSuggestion]