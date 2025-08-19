from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
import logging
from copy import deepcopy

from ....core.database import get_async_session
from ....core.dependencies import get_current_active_admin
from ....models.admin import Admin
from ....models.tournament import Tournament
from ....models.score import Score
from ....schemas.tournament import (
    TournamentCreate, TournamentUpdate, TournamentResponse, 
    TournamentListResponse, TournamentConfig
)
from ....services.audit_service import audit_service
from ....services.notification_service import notification_service, NotificationType

router = APIRouter(prefix="/tournaments", tags=["Admin - Tournaments"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=TournamentListResponse)
async def list_tournaments(
    page: int = Query(1, ge=1, description="Página"),
    size: int = Query(10, ge=1, le=100, description="Itens por página"),
    search: Optional[str] = Query(None, description="Buscar por nome"),
    active_only: bool = Query(False, description="Apenas torneios ativos"),
    session: AsyncSession = Depends(get_async_session),
    current_admin: Admin = Depends(get_current_active_admin)
):
    """Listar torneios com filtros e paginação"""
    
    query = select(Tournament)
    count_query = select(func.count(Tournament.id))
    
    if search:
        search_filter = f"%{search}%"
        query = query.where(Tournament.name.ilike(search_filter))
        count_query = count_query.where(Tournament.name.ilike(search_filter))
    
    if active_only:
        now = datetime.utcnow()
        query = query.where(Tournament.end_date >= now)
        count_query = count_query.where(Tournament.end_date >= now)
    
    total_res = await session.exec(count_query)
    total = total_res.first()
    
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(Tournament.start_date.desc())
    tournaments_res = await session.exec(query)
    tournaments = tournaments_res.all()
    
    pages = (total + size - 1) // size if total > 0 else 1
    
    logger.info(f"Listed {len(tournaments)} tournaments for admin {current_admin.email}")
    
    return TournamentListResponse(
        tournaments=[TournamentResponse.model_validate(t) for t in tournaments],
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/{tournament_id}", response_model=TournamentResponse)
async def get_tournament(
    tournament_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_admin: Admin = Depends(get_current_active_admin)
):
    """Obter torneio por ID"""
    
    tournament = await session.get(Tournament, tournament_id)
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found"
        )
    
    return TournamentResponse.model_validate(tournament)


@router.post("/", response_model=TournamentResponse, status_code=status.HTTP_201_CREATED)
async def create_tournament(
    tournament_data: TournamentCreate,
    session: AsyncSession = Depends(get_async_session),
    current_admin: Admin = Depends(get_current_active_admin)
):
    """Criar novo torneio"""
    
    if tournament_data.start_date >= tournament_data.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date"
        )
    
    existing_tournament_res = await session.exec(
        select(Tournament).where(Tournament.name == tournament_data.name)
    )
    if existing_tournament_res.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tournament with this name already exists"
        )
    
    tournament = Tournament.model_validate(tournament_data)
    
    session.add(tournament)
    await session.commit()
    await session.refresh(tournament)
    
    logger.info(f"Tournament created: {tournament.id} by admin {current_admin.email}")

    # Audit Log
    await audit_service.log_action(
        session=session,
        action="CREATE",
        table_name="tournaments",
        record_id=tournament.id,
        admin_id=current_admin.id,
        new_values=TournamentResponse.model_validate(tournament).model_dump()
    )

    # Notification
    # await notification_service.send_notification(
    #     session=session,
    #     notification_type=NotificationType.TOURNAMENT_CREATED,
    #     title=f"Novo Torneio: {tournament.name}",
    #     message=f"O torneio '{tournament.name}' foi criado.",
    #     data={'tournament_id': tournament.id, 'name': tournament.name}
    # )
    
    return TournamentResponse.model_validate(tournament)


@router.put("/{tournament_id}", response_model=TournamentResponse)
async def update_tournament(
    tournament_id: int,
    tournament_data: TournamentUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_admin: Admin = Depends(get_current_active_admin)
):
    """Atualizar torneio"""
    
    tournament = await session.get(Tournament, tournament_id)
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found"
        )
    
    old_tournament_data = TournamentResponse.model_validate(deepcopy(tournament)).model_dump()

    update_data = tournament_data.model_dump(exclude_unset=True)
    
    start_date = update_data.get('start_date', tournament.start_date)
    end_date = update_data.get('end_date', tournament.end_date)
    
    if start_date >= end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date"
        )
    
    if 'name' in update_data:
        existing_tournament_res = await session.exec(
            select(Tournament).where(
                Tournament.name == update_data['name'],
                Tournament.id != tournament_id
            )
        )
        if existing_tournament_res.first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tournament with this name already exists"
            )
    
    for field, value in update_data.items():
        setattr(tournament, field, value)
    
    tournament.updated_at = datetime.utcnow()
    
    session.add(tournament)
    await session.commit()
    await session.refresh(tournament)
    
    logger.info(f"Tournament updated: {tournament.id} by admin {current_admin.email}")

    # Audit Log
    await audit_service.log_action(
        session=session,
        action="UPDATE",
        table_name="tournaments",
        record_id=tournament.id,
        admin_id=current_admin.id,
        old_values=old_tournament_data,
        new_values=TournamentResponse.model_validate(tournament).model_dump()
    )
    
    return TournamentResponse.model_validate(tournament)


@router.delete("/{tournament_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tournament(
    tournament_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_admin: Admin = Depends(get_current_active_admin)
):
    """Deletar torneio"""
    
    tournament = await session.get(Tournament, tournament_id)
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found"
        )
    
    old_tournament_data = TournamentResponse.model_validate(deepcopy(tournament)).model_dump()

    scores_count_res = await session.exec(
        select(func.count(Score.id)).where(Score.tournament_id == tournament_id)
    )
    scores_count = scores_count_res.first()
    
    if scores_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete tournament with {scores_count} associated scores"
        )
    
    await session.delete(tournament)
    await session.commit()
    
    logger.info(f"Tournament deleted: {tournament_id} by admin {current_admin.email}")

    # Audit Log
    await audit_service.log_action(
        session=session,
        action="DELETE",
        table_name="tournaments",
        record_id=tournament_id,
        admin_id=current_admin.id,
        old_values=old_tournament_data
    )
    
    return