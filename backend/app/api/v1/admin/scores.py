from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime
import logging
from copy import deepcopy

from ....core.database import get_async_session
from ....core.dependencies import get_current_active_admin
from ....models.admin import Admin
from ....models.score import Score
from ....models.player import Player
from ....models.tournament import Tournament
from ....schemas.score import (
    ScoreCreate, ScoreUpdate, ScoreResponse, ScoreListResponse,
    ScoreImportRequest, ScoreImportResponse, ScoreWithDetails
)
from ....services.audit_service import audit_service
from ....services.import_service import import_service

router = APIRouter(prefix="/scores", tags=["Admin - Scores"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=ScoreListResponse)
async def list_scores(
    page: int = Query(1, ge=1, description="Página"),
    size: int = Query(10, ge=1, le=100, description="Itens por página"),
    player_id: Optional[int] = Query(None, description="Filtrar por jogador"),
    tournament_id: Optional[int] = Query(None, description="Filtrar por torneio"),
    search: Optional[str] = Query(None, description="Buscar por nome do jogador"),
    session: AsyncSession = Depends(get_async_session),
    current_admin: Admin = Depends(get_current_active_admin)
):
    """Listar pontuações com filtros e paginação"""
    
    query = select(Score)
    count_query = select(func.count(Score.id))
    
    if player_id:
        query = query.where(Score.player_id == player_id)
        count_query = count_query.where(Score.player_id == player_id)
    
    if tournament_id:
        query = query.where(Score.tournament_id == tournament_id)
        count_query = count_query.where(Score.tournament_id == tournament_id)
    
    if search:
        search_filter = f"%{search}%"
        query = query.join(Player).where(
            Player.name.ilike(search_filter) | 
            Player.nickname.ilike(search_filter)
        )
        count_query = count_query.join(Player).where(
            Player.name.ilike(search_filter) | 
            Player.nickname.ilike(search_filter)
        )
    
    total_res = await session.exec(count_query)
    total = total_res.first()
    
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(Score.created_at.desc())
    scores_res = await session.exec(query)
    scores = scores_res.all()
    
    pages = (total + size - 1) // size if total > 0 else 1
    
    logger.info(f"Listed {len(scores)} scores for admin {current_admin.email}")
    
    return ScoreListResponse(
        scores=[ScoreResponse.model_validate(s) for s in scores],
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.post("/", response_model=ScoreResponse, status_code=status.HTTP_201_CREATED)
async def create_score(
    score_data: ScoreCreate,
    session: AsyncSession = Depends(get_async_session),
    current_admin: Admin = Depends(get_current_active_admin)
):
    """Criar nova pontuação"""
    
    player = await session.get(Player, score_data.player_id)
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    
    tournament = await session.get(Tournament, score_data.tournament_id)
    if not tournament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    
    existing_score_res = await session.exec(
        select(Score).where(
            Score.player_id == score_data.player_id,
            Score.tournament_id == score_data.tournament_id
        )
    )
    if existing_score_res.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Score already exists for this player and tournament"
        )
    
    score = Score.model_validate(score_data, update={"admin_id": current_admin.id})
    
    session.add(score)
    await session.commit()
    await session.refresh(score)
    
    logger.info(f"Score created: {score.id} by admin {current_admin.email}")

    await audit_service.log_action(
        session=session, action="CREATE", table_name="scores",
        record_id=score.id, admin_id=current_admin.id,
        new_values=ScoreResponse.model_validate(score).model_dump()
    )
    
    return ScoreResponse.model_validate(score)


@router.put("/{score_id}", response_model=ScoreResponse)
async def update_score(
    score_id: int,
    score_data: ScoreUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_admin: Admin = Depends(get_current_active_admin)
):
    """Atualizar pontuação"""
    
    score = await session.get(Score, score_id)
    if not score:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Score not found")

    old_score_data = ScoreResponse.model_validate(deepcopy(score)).model_dump()
    
    update_data = score_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(score, field, value)
    
    score.updated_at = datetime.utcnow()
    
    session.add(score)
    await session.commit()
    await session.refresh(score)
    
    logger.info(f"Score updated: {score.id} by admin {current_admin.email}")

    await audit_service.log_action(
        session=session, action="UPDATE", table_name="scores",
        record_id=score.id, admin_id=current_admin.id,
        old_values=old_score_data,
        new_values=ScoreResponse.model_validate(score).model_dump()
    )
    
    return ScoreResponse.model_validate(score)


@router.delete("/{score_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_score(
    score_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_admin: Admin = Depends(get_current_active_admin)
):
    """Deletar pontuação"""
    
    score = await session.get(Score, score_id)
    if not score:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Score not found")

    old_score_data = ScoreResponse.model_validate(deepcopy(score)).model_dump()
    
    await session.delete(score)
    await session.commit()
    
    logger.info(f"Score deleted: {score_id} by admin {current_admin.email}")

    await audit_service.log_action(
        session=session, action="DELETE", table_name="scores",
        record_id=score_id, admin_id=current_admin.id,
        old_values=old_score_data
    )
    
    return

@router.post("/import", response_model=ScoreImportResponse)
async def import_scores(
    import_data: ScoreImportRequest,
    session: AsyncSession = Depends(get_async_session),
    current_admin: Admin = Depends(get_current_active_admin)
):
    """Importar pontuações em lote usando o ImportService."""
    
    result = await import_service.import_scores(
        session=session,
        scores_to_import=import_data.scores,
        preview_only=import_data.preview_only,
        admin_id=current_admin.id
    )

    if not import_data.preview_only and result["success"] > 0:
        await audit_service.log_action(
            session=session, action="IMPORT", table_name="scores",
            admin_id=current_admin.id,
            new_values={"count": result["success"], "errors": len(result["errors"])}
        )

    message = f"Preview completed" if import_data.preview_only else f"Import completed: {result['success']} scores created"
    
    return ScoreImportResponse(
        success=result["success"],
        errors=result["errors"],
        previewed=result["previewed"],
        message=message
    )
