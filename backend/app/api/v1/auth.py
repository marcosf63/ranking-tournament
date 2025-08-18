from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime
from typing import Dict, Any
import logging

from ...core.database import get_session
from ...core.security import verify_password, create_token_response, verify_token
from ...models.admin import Admin
from ...schemas.auth import LoginRequest, LoginResponse, TokenResponse, RefreshTokenRequest, AdminResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)

@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    session: Session = Depends(get_session)
):
    """Autenticar admin e retornar tokens JWT"""
    
    # Buscar admin por email
    admin = session.query(Admin).filter(Admin.email == login_data.email).first()
    
    if not admin:
        logger.warning(f"Login attempt with invalid email: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verificar senha
    if not verify_password(login_data.password, admin.password_hash):
        logger.warning(f"Invalid password for admin: {admin.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verificar se admin está ativo
    if not admin.is_active:
        logger.warning(f"Login attempt by inactive admin: {admin.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )
    
    # Atualizar último login
    admin.last_login = datetime.utcnow()
    session.add(admin)
    session.commit()
    session.refresh(admin)
    
    # Criar tokens
    admin_data = {"id": admin.id, "email": admin.email, "permission_level": admin.permission_level}
    tokens = create_token_response(admin_data)
    
    logger.info(f"Successful login for admin: {admin.email}")
    
    return LoginResponse(
        admin=AdminResponse(
            id=admin.id,
            name=admin.name,
            email=admin.email,
            permission_level=admin.permission_level,
            is_active=admin.is_active,
            last_login=admin.last_login.isoformat() if admin.last_login else None,
            created_at=admin.created_at.isoformat()
        ),
        tokens=TokenResponse(**tokens)
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    session: Session = Depends(get_session)
):
    """Renovar access token usando refresh token"""
    
    # Verificar refresh token
    payload = verify_token(refresh_data.refresh_token, "refresh")
    
    if payload is None:
        logger.warning("Invalid refresh token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    admin_id = payload.get("admin_id")
    if admin_id is None:
        logger.warning("Refresh token without admin_id")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Buscar admin
    admin = session.query(Admin).filter(Admin.id == admin_id, Admin.is_active == True).first()
    
    if admin is None:
        logger.warning(f"Admin not found or inactive for refresh: {admin_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Criar novos tokens
    admin_data = {"id": admin.id, "email": admin.email, "permission_level": admin.permission_level}
    tokens = create_token_response(admin_data)
    
    logger.info(f"Token refreshed for admin: {admin.email}")
    
    return TokenResponse(**tokens)

@router.post("/logout")
async def logout():
    """Logout do admin (invalidar tokens - implementação futura)"""
    # Para uma implementação completa, seria necessário uma blacklist de tokens
    # Por enquanto, apenas retorna sucesso (tokens expiram naturalmente)
    
    logger.info("Admin logout")
    
    return {"message": "Logout successful"}