from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class RankingEntry(BaseModel):
    position: int
    player_id: int
    player_name: str
    player_nickname: str
    avatar_url: Optional[str] = None
    total_points: float
    total_tournaments: int
    average_points: float
    best_score: float
    worst_score: float
    score_date: Optional[datetime] = None
    notes: Optional[str] = None


class RankingResponse(BaseModel):
    entries: List[RankingEntry]
    total: int
    page: int
    size: int
    pages: int
    ranking_type: str = "general"


class TournamentRanking(BaseModel):
    tournament_id: int
    tournament_name: str
    tournament_description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    sort_criteria: str
    entries: List[RankingEntry]
    total: int
    page: int
    size: int
    pages: int


class PlayerTournamentResult(BaseModel):
    tournament_id: int
    tournament_name: str
    points: float
    position: int
    score_date: datetime


class PlayerStats(BaseModel):
    player_id: int
    player_name: str
    player_nickname: str
    avatar_url: Optional[str] = None
    total_tournaments: int
    total_points: float
    average_points: float
    best_score: float
    worst_score: float
    positive_scores: int
    negative_scores: int
    general_position: int
    tournaments: List[dict]


class GeneralStats(BaseModel):
    total_players: int
    total_tournaments: int
    active_tournaments: int
    total_scores: int
    average_score: float
    highest_score: float
    lowest_score: float
    positive_scores: int
    negative_scores: int