from fastapi import APIRouter, Depends, Query
from sqlmodel import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime
import logging

from ....core.database import get_async_session
from ....models.player import Player
from ....models.tournament import Tournament
from ....schemas.search import (
    SearchResult, PlayerSearchResult, TournamentSearchResult,
    SearchResponse, SearchSuggestion
)

router = APIRouter(prefix="/search", tags=["Public - Search"])
logger = logging.getLogger(__name__)


async def _search_players(query: str, limit: int, session: AsyncSession) -> List[PlayerSearchResult]:
    """Helper function to search for players efficiently."""
    search_filter = f"%{query}%"
    players_query = text("""
        WITH player_ranks AS (
            SELECT 
                s.player_id, 
                SUM(s.points) as total_points,
                COUNT(s.id) as total_tournaments,
                RANK() OVER (ORDER BY SUM(s.points) DESC) as position
            FROM scores s
            GROUP BY s.player_id
        )
        SELECT 
            p.id, p.name, p.nickname, p.avatar_url,
            COALESCE(pr.total_tournaments, 0) as total_tournaments,
            COALESCE(pr.total_points, 0) as total_points,
            COALESCE(pr.position, 0) as position
        FROM players p
        LEFT JOIN player_ranks pr ON p.id = pr.player_id
        WHERE p.is_active = true
        AND (p.name ILIKE :query OR p.nickname ILIKE :query)
        ORDER BY total_points DESC
        LIMIT :limit
    ")
    
    result = await session.execute(players_query, {"query": search_filter, "limit": limit})
    return [PlayerSearchResult.model_validate(row, from_attributes=True) for row in result.mappings()]

async def _search_tournaments(query: str, limit: int, session: AsyncSession) -> List[TournamentSearchResult]:
    """Helper function to search for tournaments efficiently."""
    search_filter = f"%{query}%"
    tournaments_query = text("""
        SELECT 
            t.id, t.name, t.description, t.start_date, t.end_date,
            COUNT(DISTINCT s.player_id) as participants_count,
            (t.end_date >= NOW()) as is_active
        FROM tournaments t
        LEFT JOIN scores s ON t.id = s.tournament_id
        WHERE (t.name ILIKE :query OR t.description ILIKE :query)
        GROUP BY t.id, t.name, t.description, t.start_date, t.end_date
        ORDER BY t.start_date DESC
        LIMIT :limit
    ")
    
    result = await session.execute(tournaments_query, {"query": search_filter, "limit": limit})
    return [TournamentSearchResult.model_validate(row, from_attributes=True) for row in result.mappings()]


@router.get("/", response_model=SearchResponse)
async def search_all(
    query: str = Query(..., min_length=2, description="Termo de busca"),
    limit: int = Query(10, ge=1, le=50, description="Limite de resultados"),
    session: AsyncSession = Depends(get_async_session)
):
    """Busca geral por jogadores e torneios de forma otimizada."""
    
    player_results = await _search_players(query, limit, session)
    tournament_results = await _search_tournaments(query, limit, session)
    
    logger.info(f"Search performed: '{query}' - {len(player_results)} players, {len(tournament_results)} tournaments")
    
    return SearchResponse(
        query=query,
        players=player_results,
        tournaments=tournament_results,
        total_results=len(player_results) + len(tournament_results)
    )


@router.get("/players", response_model=List[PlayerSearchResult])
async def search_players(
    query: str = Query(..., min_length=2, description="Termo de busca"),
    limit: int = Query(20, ge=1, le=100, description="Limite de resultados"),
    session: AsyncSession = Depends(get_async_session)
):
    """Busca específica por jogadores"""
    players = await _search_players(query, limit, session)
    logger.info(f"Player search: '{query}' - {len(players)} results")
    return players


@router.get("/tournaments", response_model=List[TournamentSearchResult])
async def search_tournaments(
    query: str = Query(..., min_length=2, description="Termo de busca"),
    active_only: bool = Query(False, description="Apenas torneios ativos"),
    limit: int = Query(20, ge=1, le=100, description="Limite de resultados"),
    session: AsyncSession = Depends(get_async_session)
):
    """Busca específica por torneios"""
    search_filter = f"%{query}%"
    where_clause = "WHERE (t.name ILIKE :query OR t.description ILIKE :query)"
    if active_only:
        where_clause += " AND t.end_date >= NOW()"
    
    tournaments_query = text(f"""
        SELECT 
            t.id, t.name, t.description, t.start_date, t.end_date,
            COUNT(DISTINCT s.player_id) as participants_count,
            (t.end_date >= NOW()) as is_active
        FROM tournaments t
        LEFT JOIN scores s ON t.id = s.tournament_id
        {where_clause}
        GROUP BY t.id, t.name, t.description, t.start_date, t.end_date
        ORDER BY t.start_date DESC
        LIMIT :limit
    ")
    
    result = await session.execute(tournaments_query, {"query": search_filter, "limit": limit})
    tournaments = [TournamentSearchResult.model_validate(row, from_attributes=True) for row in result.mappings()]
    
    logger.info(f"Tournament search: '{query}' - {len(tournaments)} results")
    return tournaments


@router.get("/suggestions", response_model=List[SearchSuggestion])
async def get_search_suggestions(
    query: str = Query(..., min_length=1, description="Termo de busca"),
    limit: int = Query(5, ge=1, le=10, description="Limite de sugestões"),
    session: AsyncSession = Depends(get_async_session)
):
    """Obter sugestões de busca"""
    search_filter = f"{query}%"
    
    player_query = text("""
        (SELECT name as text, 'player' as type FROM players WHERE is_active = true AND name ILIKE :query)
        UNION
        (SELECT nickname as text, 'player' as type FROM players WHERE is_active = true AND nickname ILIKE :query)
        LIMIT :limit
    ")
    player_res = await session.execute(player_query, {"query": search_filter, "limit": limit})
    
    tournament_query = text("""
        SELECT name as text, 'tournament' as type FROM tournaments WHERE name ILIKE :query
        LIMIT :limit
    ")
    tournament_res = await session.execute(tournament_query, {"query": search_filter, "limit": limit})

    suggestions = [SearchSuggestion(text=row.text, type=row.type) for row in player_res.mappings()] \
                  + [SearchSuggestion(text=row.text, type=row.type) for row in tournament_res.mappings()]

    # Remove duplicates and limit
    seen = set()
    unique_suggestions = []
    for s in suggestions:
        if s.text.lower() not in seen:
            unique_suggestions.append(s)
            seen.add(s.text.lower())
        if len(unique_suggestions) >= limit:
            break

    logger.info(f"Search suggestions for '{query}': {len(unique_suggestions)} results")
    return unique_suggestions
