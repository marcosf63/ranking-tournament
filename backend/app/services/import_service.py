
"""
Serviço para lógica de negócio de importação de dados em lote.
"""
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import logging

from ..models.player import Player
from ..models.score import Score
from ..models.tournament import Tournament
from ..schemas.player import PlayerImportItem, PlayerResponse
from ..schemas.score import ScoreImportItem, ScoreResponse

logger = logging.getLogger(__name__)

class ImportService:

    async def import_players(
        self, 
        session: AsyncSession, 
        players_to_import: List[PlayerImportItem], 
        preview_only: bool
    ) -> Dict[str, Any]:
        """Processa a importação de jogadores em lote."""
        success_count = 0
        errors = []
        previewed_players = []

        for i, player_item in enumerate(players_to_import):
            try:
                existing_nick = (await session.exec(select(Player).where(Player.nickname == player_item.nickname))).first()
                if existing_nick:
                    errors.append(f"Line {i+1}: Nickname '{player_item.nickname}' already exists")
                    continue
                
                if player_item.email:
                    existing_email = (await session.exec(select(Player).where(Player.email == player_item.email))).first()
                    if existing_email:
                        errors.append(f"Line {i+1}: Email '{player_item.email}' already exists")
                        continue

                player = Player.model_validate(player_item)
                if preview_only:
                    player.id = i + 1000  # Fake ID for preview
                    previewed_players.append(PlayerResponse.model_validate(player))
                else:
                    session.add(player)
                    await session.flush()
                    previewed_players.append(PlayerResponse.model_validate(player))
                    success_count += 1

            except Exception as e:
                errors.append(f"Line {i+1}: An unexpected error occurred: {str(e)}")

        if not preview_only:
            if errors:
                await session.rollback()
                logger.warning(f"Player import failed with {len(errors)} errors. Rolling back transaction.")
                success_count = 0
                previewed_players = []
            else:
                await session.commit()
                logger.info(f"Committed {success_count} new players.")
        
        return {"success": success_count, "errors": errors, "previewed": previewed_players}

    async def import_scores(
        self,
        session: AsyncSession,
        scores_to_import: List[ScoreImportItem],
        preview_only: bool,
        admin_id: int
    ) -> Dict[str, Any]:
        """Processa a importação de pontuações em lote."""
        success_count = 0
        errors = []
        previewed_scores = []

        for i, score_item in enumerate(scores_to_import):
            try:
                player = await session.get(Player, score_item.player_id)
                if not player:
                    errors.append(f"Line {i+1}: Player with ID {score_item.player_id} not found.")
                    continue

                tournament = await session.get(Tournament, score_item.tournament_id)
                if not tournament:
                    errors.append(f"Line {i+1}: Tournament with ID {score_item.tournament_id} not found.")
                    continue

                existing_score = (await session.exec(select(Score).where(
                    Score.player_id == score_item.player_id,
                    Score.tournament_id == score_item.tournament_id
                ))).first()

                if existing_score and not preview_only:
                    errors.append(f"Line {i+1}: Score already exists for player {player.nickname} in tournament {tournament.name}.")
                    continue

                score = Score.model_validate(score_item, update={"admin_id": admin_id})
                if preview_only:
                    score.id = i + 1000 # Fake ID
                    previewed_scores.append(ScoreResponse.model_validate(score))
                else:
                    session.add(score)
                    success_count += 1

            except Exception as e:
                errors.append(f"Line {i+1}: An unexpected error occurred: {str(e)}")

        if not preview_only:
            if errors:
                await session.rollback()
                logger.warning(f"Score import failed with {len(errors)} errors. Rolling back transaction.")
                success_count = 0
            else:
                await session.commit()
                logger.info(f"Committed {success_count} new scores.")

        return {"success": success_count, "errors": errors, "previewed": previewed_scores}


# Instância global do serviço
import_service = ImportService()
