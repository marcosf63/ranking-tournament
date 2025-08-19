from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from math import ceil
import logging
from copy import deepcopy

from ....core.database import get_async_session
from ....core.dependencies import get_current_active_admin
from ....models.player import Player
from ....models.admin import Admin
from ....schemas.player import (
    PlayerCreate, PlayerUpdate, PlayerResponse, PlayerListResponse,
    PlayerImportRequest, PlayerImportResponse
)
from ....services.audit_service import audit_service
from ....services.import_service import import_service

router = APIRouter(prefix="/players", tags=["Admin - Players"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=PlayerListResponse)
async def list_players(
    page: int = Query(1, ge=1, description="Página"),
    size: int = Query(10, ge=1, le=100, description="Itens por página"),
    search: Optional[str] = Query(None, description="Busca por nome ou nickname"),
    active_only: bool = Query(True, description="Apenas jogadores ativos"),
    session: AsyncSession = Depends(get_async_session),
    current_admin: Admin = Depends(get_current_active_admin)
):
    """Listar jogadores com paginação e filtros"""
    
    query = select(Player)
    count_query = select(func.count(Player.id))

    if active_only:
        query = query.where(Player.is_active == True)
        count_query = count_query.where(Player.is_active == True)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Player.name.ilike(search_term)) | 
            (Player.nickname.ilike(search_term))
        )
        count_query = count_query.where(
            (Player.name.ilike(search_term)) | 
            (Player.nickname.ilike(search_term))
        )
    
    total_res = await session.exec(count_query)
    total = total_res.first()
    
    offset = (page - 1) * size
    players_res = await session.exec(query.offset(offset).limit(size).order_by(Player.name))
    players = players_res.all()
    
    pages = ceil(total / size) if total > 0 else 1
    
    logger.info(f"Listed {len(players)} players (page {page}/{pages}) by admin {current_admin.email}")
    
    return PlayerListResponse(
        players=[PlayerResponse.model_validate(p) for p in players],
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.post("/", response_model=PlayerResponse, status_code=status.HTTP_201_CREATED)
async def create_player(
    player_data: PlayerCreate,
    session: AsyncSession = Depends(get_async_session),
    current_admin: Admin = Depends(get_current_active_admin)
):
    """Criar novo jogador"""
    
    existing_player_res = await session.exec(select(Player).where(Player.nickname == player_data.nickname))
    if existing_player_res.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nickname already exists"
        )
    
    if player_data.email:
        existing_email_res = await session.exec(select(Player).where(Player.email == player_data.email))
        if existing_email_res.first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    player = Player.model_validate(player_data)
    session.add(player)
    await session.commit()
    await session.refresh(player)
    
    logger.info(f"Player created: {player.nickname} by admin {current_admin.email}")

    await audit_service.log_action(
        session=session, action="CREATE", table_name="players",
        record_id=player.id, admin_id=current_admin.id,
        new_values=PlayerResponse.model_validate(player).model_dump()
    )
    
    return PlayerResponse.model_validate(player)


@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(
    player_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_admin: Admin = Depends(get_current_active_admin)
):
    """Obter detalhes de um jogador"""
    
    player = await session.get(Player, player_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    return PlayerResponse.model_validate(player)


@router.put("/{player_id}", response_model=PlayerResponse)
async def update_player(
    player_id: int,
    player_data: PlayerUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_admin: Admin = Depends(get_current_active_admin)
):
    """Atualizar jogador"""
    
    player = await session.get(Player, player_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )

    old_player_data = PlayerResponse.model_validate(deepcopy(player)).model_dump()
    
    update_data = player_data.model_dump(exclude_unset=True)
    
    if "nickname" in update_data and update_data["nickname"] != player.nickname:
        existing_res = await session.exec(select(Player).where(
            Player.nickname == update_data["nickname"],
            Player.id != player_id
        ))
        if existing_res.first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nickname already exists"
            )
    
    if "email" in update_data and update_data["email"] and update_data["email"] != player.email:
        existing_res = await session.exec(select(Player).where(
            Player.email == update_data["email"],
            Player.id != player_id
        ))
        if existing_res.first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    for field, value in update_data.items():
        setattr(player, field, value)
    
    session.add(player)
    await session.commit()
    await session.refresh(player)
    
    logger.info(f"Player updated: {player.nickname} by admin {current_admin.email}")

    await audit_service.log_action(
        session=session, action="UPDATE", table_name="players",
        record_id=player.id, admin_id=current_admin.id,
        old_values=old_player_data,
        new_values=PlayerResponse.model_validate(player).model_dump()
    )
    
    return PlayerResponse.model_validate(player)


@router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_player(
    player_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_admin: Admin = Depends(get_current_active_admin)
):
    """Desativar jogador (soft delete)"""
    
    player = await session.get(Player, player_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )

    old_player_data = PlayerResponse.model_validate(deepcopy(player)).model_dump()
    
    player.is_active = False
    session.add(player)
    await session.commit()
    
    logger.info(f"Player deactivated: {player.nickname} by admin {current_admin.email}")

    await audit_service.log_action(
        session=session, action="DEACTIVATE", table_name="players",
        record_id=player.id, admin_id=current_admin.id,
        old_values=old_player_data,
        new_values=PlayerResponse.model_validate(player).model_dump()
    )
    
    return

@router.post("/import", response_model=PlayerImportResponse)
async def import_players(
    import_data: PlayerImportRequest,
    session: AsyncSession = Depends(get_async_session),
    current_admin: Admin = Depends(get_current_active_admin)
):
    """Importar jogadores em lote usando o ImportService."""
    
    result = await import_service.import_players(
        session=session,
        players_to_import=import_data.players,
        preview_only=import_data.preview_only
    )

    if not import_data.preview_only and result["success"] > 0:
        await audit_service.log_action(
            session=session, action="IMPORT", table_name="players",
            admin_id=current_admin.id,
            new_values={"count": result["success"], "errors": len(result["errors"])}
        )

    message = "Preview completed" if import_data.preview_only else f"Import completed: {result['success']} players created"
    
    return PlayerImportResponse(
        success=result["success"],
        errors=result["errors"],
        previewed=result["previewed"],
        message=message
    )
