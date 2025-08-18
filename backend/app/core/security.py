from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from .config import settings
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Criar token de acesso JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Criar token de refresh JWT"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """Verificar e decodificar token JWT"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        
        # Verificar tipo do token
        if payload.get("type") != token_type:
            return None
            
        # Verificar expiração
        exp = payload.get("exp")
        if exp is None or datetime.fromtimestamp(exp) < datetime.utcnow():
            return None
            
        return payload
    except JWTError as e:
        logger.warning(f"JWT Error: {e}")
        return None

def get_password_hash(password: str) -> str:
    """Gerar hash da senha"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar senha contra hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_token_response(admin_data: Dict[str, Any]) -> Dict[str, Any]:
    """Criar resposta completa com tokens"""
    access_token = create_access_token(data={"sub": str(admin_data["id"]), "admin_id": admin_data["id"]})
    refresh_token = create_refresh_token(data={"sub": str(admin_data["id"]), "admin_id": admin_data["id"]})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60
    }