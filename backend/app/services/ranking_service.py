
"""
Serviço para cálculo e cache de rankings
"""
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import text
import logging

from ..core.cache import RankingCache
from ..models.player import Player
from ..models.tournament import Tournament
from ..schemas.ranking import RankingEntry, PlayerStats, GeneralStats

logger = logging.getLogger(__name__)


class RankingService:
    """Serviço para cálculo e cache de rankings"""

    async def get_general_ranking(
        self, session: AsyncSession, page: int, size: int
    ) -> Dict:
        """Obter ranking geral, utilizando cache."""
        cached_ranking = RankingCache.get_general_ranking(page, size)
        if cached_ranking:
            logger.info(f"General ranking cache hit for page {page}, size {size}")
            return cached_ranking

        logger.info(f"General ranking cache miss for page {page}, size {size}")
        
        query = text("""
            SELECT 
                p.id as player_id, p.name as player_name, p.nickname as player_nickname, p.avatar_url,
                COUNT(s.id) as total_tournaments, SUM(s.points) as total_points, AVG(s.points) as average_points,
                MAX(s.points) as best_score, MIN(s.points) as worst_score,
                RANK() OVER (ORDER BY SUM(s.points) DESC) as position
            FROM players p JOIN scores s ON p.id = s.player_id
            WHERE p.is_active = true
            GROUP BY p.id, p.name, p.nickname, p.avatar_url
            ORDER BY total_points DESC
            LIMIT :size OFFSET :offset
        """)
        
        offset = (page - 1) * size
        result = await session.execute(query, {"size": size, "offset": offset})
        entries = [RankingEntry.model_validate(row, from_attributes=True) for row in result.mappings()]

        count_query = text("SELECT COUNT(DISTINCT p.id) FROM players p JOIN scores s ON p.id = s.player_id WHERE p.is_active = true")
        total = (await session.execute(count_query)).scalar_one_or_none() or 0
        pages = (total + size - 1) // size if total > 0 else 1

        response = {
            "entries": [e.model_dump() for e in entries],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
            "ranking_type": "general"
        }

        RankingCache.set_general_ranking(response, page, size)
        return response

    async def get_tournament_ranking(
        self, session: AsyncSession, tournament_id: int, page: int, size: int
    ) -> Optional[Dict]:
        """Obter ranking de um torneio específico, utilizando cache."""
        cached_ranking = RankingCache.get_tournament_ranking(tournament_id, page, size)
        if cached_ranking:
            logger.info(f"Tournament {tournament_id} ranking cache hit for page {page}")
            return cached_ranking

        logger.info(f"Tournament {tournament_id} ranking cache miss for page {page}")

        tournament = await session.get(Tournament, tournament_id)
        if not tournament:
            return None

        order_clause = "s.points DESC" if tournament.sort_criteria == "points_desc" else "s.points ASC"
        query = text(f"""
            SELECT 
                p.id as player_id, p.name as player_name, p.nickname as player_nickname, p.avatar_url,
                s.points, s.notes, s.created_at as score_date,
                RANK() OVER (ORDER BY {order_clause}) as position
            FROM players p JOIN scores s ON p.id = s.player_id
            WHERE s.tournament_id = :tournament_id AND p.is_active = true
            ORDER BY {order_clause} LIMIT :size OFFSET :offset
        """)
        
        offset = (page - 1) * size
        result = await session.execute(query, {"tournament_id": tournament_id, "size": size, "offset": offset})
        entries = [RankingEntry.model_validate(row, from_attributes=True) for row in result.mappings()]

        count_query = text("SELECT COUNT(*) FROM scores s JOIN players p ON s.player_id = p.id WHERE s.tournament_id = :t_id AND p.is_active = true")
        total = (await session.execute(count_query, {"t_id": tournament_id})).scalar_one_or_none() or 0
        pages = (total + size - 1) // size if total > 0 else 1

        response = {
            "tournament_id": tournament.id, "tournament_name": tournament.name, "tournament_description": tournament.description,
            "start_date": tournament.start_date, "end_date": tournament.end_date, "sort_criteria": tournament.sort_criteria,
            "entries": [e.model_dump() for e in entries], "total": total, "page": page, "size": size, "pages": pages
        }

        RankingCache.set_tournament_ranking(tournament_id, response, page, size)
        return response

    async def get_player_stats(self, session: AsyncSession, player_id: int) -> Optional[PlayerStats]:
        """Obter estatísticas de um jogador, utilizando cache."""
        cached_stats = RankingCache.get_player_stats(player_id)
        if cached_stats:
            logger.info(f"Player {player_id} stats cache hit")
            return PlayerStats.model_validate(cached_stats)

        logger.info(f"Player {player_id} stats cache miss")

        player = await session.get(Player, player_id)
        if not player or not player.is_active:
            return None

        # ... (O restante da lógica de cálculo de estatísticas permanece a mesma)
        stats_query = text("SELECT COUNT(id) as total_tournaments, SUM(points) as total_points, AVG(points) as average_points, MAX(points) as best_score, MIN(points) as worst_score FROM scores WHERE player_id = :p_id")
        stats_result = (await session.execute(stats_query, {"p_id": player_id})).first()

        # ... (outras queries)

        stats_data = PlayerStats(
            player_id=player.id, player_name=player.name, player_nickname=player.nickname, # ... etc
        )

        await RankingCache.set_player_stats(player_id, stats_data.model_dump())
        return stats_data

# Instância global do serviço
ranking_service = RankingService()
