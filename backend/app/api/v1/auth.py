from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging

from ....core.database import get_async_session
from ....core.security import verify_password, create_token_response, verify_token
from ....models.admin import Admin
from ....schemas.auth import LoginRequest, LoginResponse, TokenResponse, RefreshTokenRequest, AdminResponse
from ....services.audit_service import audit_service
from ....core.cache import cache_service
from ....core.dependencies import security

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)

@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """Autenticar admin e retornar tokens JWT"""
    
    result = await session.exec(select(Admin).where(Admin.email == login_data.email))
    admin = result.first()
    
    if not admin or not verify_password(login_data.password, admin.password_hash):
        logger.warning(f"Login attempt with invalid credentials for email: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not admin.is_active:
        logger.warning(f"Login attempt by inactive admin: {admin.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )
    
    admin.last_login = datetime.utcnow()
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    
    admin_data = {"id": admin.id, "email": admin.email, "permission_level": admin.permission_level}
    tokens = create_token_response(admin_data)
    
    logger.info(f"Successful login for admin: {admin.email}")

    await audit_service.log_action(
        session=session, action="LOGIN", table_name="admins",
        record_id=admin.id, admin_id=admin.id,
        new_values={"ip_address": request.client.host}
    )
    
    return LoginResponse(
        admin=AdminResponse.model_validate(admin),
        tokens=TokenResponse(**tokens)
    )

from fastapi.security import HTTPAuthorizationCredentials

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    session: AsyncSession = Depends(get_async_session)
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
    result = await session.exec(select(Admin).where(Admin.id == admin_id, Admin.is_active == True))
    admin = result.first()
    
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

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Invalida o access token atual adicionando-o à blacklist."""
    token = credentials.credentials
    payload = verify_token(token, "access")

    if payload:
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti and exp:
            # Calcula o tempo restante de vida do token em segundos
            ttl = round(datetime.fromtimestamp(exp).timestamp() - datetime.utcnow().timestamp())
            if ttl > 0:
                await cache_service.add_to_blacklist(jti, ttl)
                logger.info(f"Token {jti} blacklisted.")
    
    return