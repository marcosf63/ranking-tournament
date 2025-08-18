from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from typing import Optional
from math import ceil
import logging

from ....core.database import get_session
from ....core.dependencies import get_current_active_admin
from ....models.player import Player
from ....models.admin import Admin
from ....schemas.player import (
    PlayerCreate, PlayerUpdate, PlayerResponse, PlayerListResponse,
    PlayerImportRequest, PlayerImportResponse
)

router = APIRouter(prefix="/players", tags=["Admin - Players"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=PlayerListResponse)
async def list_players(
    page: int = Query(1, ge=1, description="Página"),
    size: int = Query(10, ge=1, le=100, description="Itens por página"),
    search: Optional[str] = Query(None, description="Busca por nome ou nickname"),
    active_only: bool = Query(True, description="Apenas jogadores ativos"),
    session: Session = Depends(get_session),
    current_admin: Admin = Depends(get_current_active_admin)
):
    """Listar jogadores com paginação e filtros"""
    
    # Base query
    query = session.query(Player)
    
    # Filtros
    if active_only:
        query = query.filter(Player.is_active == True)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Player.name.ilike(search_term)) | 
            (Player.nickname.ilike(search_term))
        )
    
    # Contagem total
    total = query.count()
    
    # Paginação
    offset = (page - 1) * size
    players = query.offset(offset).limit(size).all()
    
    pages = ceil(total / size) if total > 0 else 1
    
    logger.info(f"Listed {len(players)} players (page {page}/{pages}) by admin {current_admin.email}")
    
    return PlayerListResponse(
        players=[PlayerResponse.model_validate(player) for player in players],
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.post("/", response_model=PlayerResponse)
async def create_player(
    player_data: PlayerCreate,
    session: Session = Depends(get_session),
    current_admin: Admin = Depends(get_current_active_admin)
):
    """Criar novo jogador"""
    
    # Verificar se nickname já existe
    existing_player = session.query(Player).filter(Player.nickname == player_data.nickname).first()
    if existing_player:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nickname already exists"
        )
    
    # Verificar se email já existe (se fornecido)
    if player_data.email:
        existing_email = session.query(Player).filter(Player.email == player_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # Criar jogador
    player = Player(**player_data.model_dump())
    session.add(player)
    session.commit()
    session.refresh(player)
    
    logger.info(f"Player created: {player.nickname} by admin {current_admin.email}")
    
    return PlayerResponse.model_validate(player)


@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(
    player_id: int,
    session: Session = Depends(get_session),
    current_admin: Admin = Depends(get_current_active_admin)
):
    """Obter detalhes de um jogador"""
    
    player = session.query(Player).filter(Player.id == player_id).first()
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
    session: Session = Depends(get_session),
    current_admin: Admin = Depends(get_current_active_admin)
):
    """Atualizar jogador"""
    
    player = session.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    update_data = player_data.model_dump(exclude_unset=True)
    
    # Verificar duplicatas antes de atualizar
    if "nickname" in update_data and update_data["nickname"] != player.nickname:
        existing = session.query(Player).filter(
            Player.nickname == update_data["nickname"],
            Player.id != player_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nickname already exists"
            )
    
    if "email" in update_data and update_data["email"] and update_data["email"] != player.email:
        existing = session.query(Player).filter(
            Player.email == update_data["email"],
            Player.id != player_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # Atualizar campos
    for field, value in update_data.items():
        setattr(player, field, value)
    
    session.add(player)
    session.commit()
    session.refresh(player)
    
    logger.info(f"Player updated: {player.nickname} by admin {current_admin.email}")
    
    return PlayerResponse.model_validate(player)


@router.delete("/{player_id}")
async def delete_player(
    player_id: int,
    session: Session = Depends(get_session),
    current_admin: Admin = Depends(get_current_active_admin)
):
    """Desativar jogador (soft delete)"""
    
    player = session.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    # TODO: Verificar se jogador tem pontuações ativas
    # Por enquanto, apenas desativa
    player.is_active = False
    session.add(player)
    session.commit()
    
    logger.info(f"Player deactivated: {player.nickname} by admin {current_admin.email}")
    
    return {"message": "Player deactivated successfully"}


@router.post("/import", response_model=PlayerImportResponse)
async def import_players(
    import_data: PlayerImportRequest,
    session: Session = Depends(get_session),
    current_admin: Admin = Depends(get_current_active_admin)
):
    """Importar jogadores em lote"""
    
    success_count = 0
    errors = []
    previewed = []
    
    for i, player_item in enumerate(import_data.players):
        try:
            # Verificar duplicatas
            existing = session.query(Player).filter(Player.nickname == player_item.nickname).first()
            if existing:
                errors.append(f"Line {i+1}: Nickname '{player_item.nickname}' already exists")
                continue
            
            if player_item.email:
                existing_email = session.query(Player).filter(Player.email == player_item.email).first()
                if existing_email:
                    errors.append(f"Line {i+1}: Email '{player_item.email}' already exists")
                    continue
            
            # Se é apenas preview, não salva
            if import_data.preview_only:
                preview_player = Player(**player_item.model_dump())
                preview_player.id = i + 1000  # ID fictício para preview
                previewed.append(PlayerResponse.model_validate(preview_player))
                continue
            
            # Criar jogador
            player = Player(**player_item.model_dump())
            session.add(player)
            session.flush()  # Para obter o ID
            session.refresh(player)
            previewed.append(PlayerResponse.model_validate(player))
            success_count += 1
            
        except Exception as e:
            errors.append(f"Line {i+1}: {str(e)}")
    
    if not import_data.preview_only:
        session.commit()
        logger.info(f"Imported {success_count} players by admin {current_admin.email}")
    
    message = "Preview completed" if import_data.preview_only else f"Import completed: {success_count} players created"
    
    return PlayerImportResponse(
        success=success_count,
        errors=errors,
        previewed=previewed,
        message=message
    )