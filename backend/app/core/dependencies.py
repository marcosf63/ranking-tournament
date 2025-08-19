from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from .database import get_async_session
from .security import verify_token
from ..models.admin import Admin
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
) -> Admin:
    """Dependência para obter o admin atual autenticado"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = verify_token(token, "access")
    
    if payload is None:
        logger.warning("Invalid token provided")
        raise credentials_exception

    # Check if token is blacklisted
    jti = payload.get("jti")
    if not jti or await cache_service.is_in_blacklist(jti):
        logger.warning(f"Blacklisted token used for admin_id: {payload.get('admin_id')}")
        raise credentials_exception
        
    admin_id = payload.get("admin_id")
    if admin_id is None:
        logger.warning("Token without admin_id")
        raise credentials_exception
    
    # Buscar admin no banco
    result = await session.exec(select(Admin).where(Admin.id == admin_id, Admin.is_active == True))
    admin = result.first()
    
    if admin is None:
        logger.warning(f"Admin not found or inactive: {admin_id}")
        raise credentials_exception
        
    return admin

async def get_current_active_admin(
    current_admin: Admin = Depends(get_current_admin)
) -> Admin:
    """Dependência para garantir que o admin está ativo"""
    if not current_admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive admin"
        )
    return current_admin

async def require_admin_level(
    current_admin: Admin = Depends(get_current_active_admin)
) -> Admin:
    """Dependência para garantir nível admin (não moderator)"""
    if current_admin.permission_level != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin level required."
        )
    return current_admin

async def get_optional_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_async_session)
) -> Optional[Admin]:
    """Dependência para obter admin atual (opcional)"""
    if not credentials:
        return None
        
    try:
        token = credentials.credentials
        payload = verify_token(token, "access")
        
        if payload is None:
            return None
            
        admin_id = payload.get("admin_id")
        if admin_id is None:
            return None
        
        # Buscar admin no banco
        result = await session.exec(select(Admin).where(Admin.id == admin_id, Admin.is_active == True))
        admin = result.first()
        
        return admin
    except Exception:
        return None
