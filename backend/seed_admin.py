#!/usr/bin/env python3
"""
Script para criar um usuário admin inicial
"""

import asyncio
import sys
import os
from passlib.context import CryptContext

# Add the app directory to the Python path
sys.path.append(os.path.dirname(__file__))

from app.core.database import get_session, SessionLocal
from app.models.admin import Admin

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin():
    """Criar admin inicial"""
    
    session = SessionLocal()
    try:
        # Verificar se já existe um admin
        existing_admin = session.query(Admin).filter_by(email="admin@ranking.com").first()
        if existing_admin:
            print("Admin já existe com email: admin@ranking.com")
            return
        
        # Criar novo admin
        hashed_password = pwd_context.hash("admin123")
        
        admin = Admin(
            name="Administrator",
            email="admin@ranking.com",
            password_hash=hashed_password,
            permission_level="admin",
            is_active=True
        )
        
        session.add(admin)
        session.commit()
        
        print("Admin criado com sucesso!")
        print("Email: admin@ranking.com")
        print("Senha: admin123")
        print("IMPORTANTE: Altere a senha após o primeiro login!")
        
    except Exception as e:
        session.rollback()
        print(f"Erro ao criar admin: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    create_admin()