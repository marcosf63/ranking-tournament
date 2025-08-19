from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ....core.database import get_async_session
from ....schemas.ranking import RankingResponse, TournamentRanking, PlayerStats, GeneralStats
from ....services.ranking_service import ranking_service

router = APIRouter(prefix="/ranking", tags=["Public - Ranking"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=RankingResponse)
async def get_general_ranking(
    page: int = Query(1, ge=1, description="Página"),
    size: int = Query(10, ge=1, le=100, description="Itens por página"),
    session: AsyncSession = Depends(get_async_session)
):
    """Obter ranking geral (todos os torneios) a partir do serviço de ranking."""
    ranking_data = await ranking_service.get_general_ranking(session, page, size)
    return RankingResponse.model_validate(ranking_data)


@router.get("/tournament/{tournament_id}", response_model=TournamentRanking)
async def get_tournament_ranking(
    tournament_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session)
):
    """Obter ranking de um torneio específico a partir do serviço de ranking."""
    ranking_data = await ranking_service.get_tournament_ranking(session, tournament_id, page, size)
    if not ranking_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found"
        )
    return TournamentRanking.model_validate(ranking_data)


@router.get("/player/{player_id}/stats", response_model=PlayerStats)
async def get_player_stats(
    player_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Obter estatísticas de um jogador a partir do serviço de ranking."""
    stats_data = await ranking_service.get_player_stats(session, player_id)
    if not stats_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found or is inactive"
        )
    return stats_data

# O endpoint de estatísticas gerais pode permanecer aqui por enquanto,
# ou ser movido para um `SystemStatsService` no futuro.
@router.get("/stats", response_model=GeneralStats)
async def get_general_stats(session: AsyncSession = Depends(get_async_session)):
    # ... (a implementação atual pode ser mantida ou movida para um serviço)
    from sqlmodel import text
    stats_query = text("""
        SELECT 
            COUNT(DISTINCT p.id) as total_players,
            COUNT(DISTINCT t.id) as total_tournaments,
            COUNT(s.id) as total_scores,
            AVG(s.points) as average_score,
            MAX(s.points) as highest_score,
            MIN(s.points) as lowest_score
        FROM players p
        LEFT JOIN scores s ON p.id = s.player_id
        LEFT JOIN tournaments t ON s.tournament_id = t.id
        WHERE p.is_active = true
    """)
    result = (await session.execute(stats_query)).first()

    active_tournaments_query = text("SELECT COUNT(*) FROM tournaments t WHERE t.end_date >= NOW()")
    active_tournaments = (await session.execute(active_tournaments_query)).scalar_one_or_none() or 0
    
    logger.info("General stats requested")
    
    return GeneralStats(
        total_players=result.total_players or 0,
        total_tournaments=result.total_tournaments or 0,
        active_tournaments=active_tournaments,
        total_scores=result.total_scores or 0,
        average_score=float(result.average_score or 0),
        highest_score=float(result.highest_score or 0),
        lowest_score=float(result.lowest_score or 0),
        positive_scores=0, 
        negative_scores=0
    )