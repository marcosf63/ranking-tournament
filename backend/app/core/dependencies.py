from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from typing import Optional
from .database import get_session
from .security import verify_token
from ..models.admin import Admin
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
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
        
    admin_id = payload.get("admin_id")
    if admin_id is None:
        logger.warning("Token without admin_id")
        raise credentials_exception
    
    # Buscar admin no banco
    admin = session.query(Admin).filter(Admin.id == admin_id, Admin.is_active == True).first()
    
    if admin is None:
        logger.warning(f"Admin not found or inactive: {admin_id}")
        raise credentials_exception
        
    return admin

def get_current_active_admin(
    current_admin: Admin = Depends(get_current_admin)
) -> Admin:
    """Dependência para garantir que o admin está ativo"""
    if not current_admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive admin"
        )
    return current_admin

def require_admin_level(
    current_admin: Admin = Depends(get_current_active_admin)
) -> Admin:
    """Dependência para garantir nível admin (não moderator)"""
    if current_admin.permission_level != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin level required."
        )
    return current_admin

def get_optional_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: Session = Depends(get_session)
) -> Optional[Admin]:
    """Dependência para obter admin atual (opcional)"""
    if not credentials:
        return None
        
    token = credentials.credentials
    payload = verify_token(token, "access")
    
    if payload is None:
        return None
        
    admin_id = payload.get("admin_id")
    if admin_id is None:
        return None
    
    # Buscar admin no banco
    admin = session.query(Admin).filter(Admin.id == admin_id, Admin.is_active == True).first()
    
    return admin