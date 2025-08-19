from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
import logging
from copy import deepcopy

from ....core.database import get_async_session
from ....core.dependencies import require_admin_level, get_current_active_admin
from ....core.security import get_password_hash, verify_password
from ....models.admin import Admin
from ....schemas.admin import (
    AdminCreate, AdminUpdate, AdminResponse, AdminListResponse,
    AdminPasswordUpdate, AdminStats
)
from ....services.audit_service import audit_service

router = APIRouter(prefix="/admins", tags=["Admin - Administrators"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
async def create_admin(
    admin_data: AdminCreate,
    session: AsyncSession = Depends(get_async_session),
    current_admin: Admin = Depends(require_admin_level)
):
    """Criar novo administrador (apenas super admin)"""
    
    existing_admin_res = await session.exec(select(Admin).where(Admin.email == admin_data.email))
    if existing_admin_res.first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    password_hash = get_password_hash(admin_data.password)
    admin = Admin.model_validate(admin_data, update={"password_hash": password_hash})
    
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    
    logger.info(f"Admin created: {admin.id} by super admin {current_admin.email}")

    await audit_service.log_action(
        session=session, action="CREATE", table_name="admins",
        record_id=admin.id, admin_id=current_admin.id,
        new_values=AdminResponse.model_validate(admin).model_dump()
    )
    
    return AdminResponse.model_validate(admin)


@router.put("/{admin_id}", response_model=AdminResponse)
async def update_admin(
    admin_id: int,
    admin_data: AdminUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_admin: Admin = Depends(require_admin_level)
):
    """Atualizar administrador (apenas super admin)"""
    
    admin = await session.get(Admin, admin_id)
    if not admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")

    if admin_id == current_admin.id and admin_data.is_active == False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate yourself")

    old_admin_data = AdminResponse.model_validate(deepcopy(admin)).model_dump()
    
    update_data = admin_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(admin, field, value)
    
    admin.updated_at = datetime.utcnow()
    
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    
    logger.info(f"Admin updated: {admin.id} by super admin {current_admin.email}")

    await audit_service.log_action(
        session=session, action="UPDATE", table_name="admins",
        record_id=admin.id, admin_id=current_admin.id,
        old_values=old_admin_data,
        new_values=AdminResponse.model_validate(admin).model_dump()
    )
    
    return AdminResponse.model_validate(admin)


@router.delete("/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin(
    admin_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_admin: Admin = Depends(require_admin_level)
):
    """Deletar administrador (apenas super admin)"""
    
    admin = await session.get(Admin, admin_id)
    if not admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")

    if admin_id == current_admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")

    if admin.permission_level == "admin":
        count_res = await session.exec(select(func.count(Admin.id)).where(Admin.permission_level == "admin", Admin.is_active == True))
        if count_res.first() <= 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete the last super admin")

    old_admin_data = AdminResponse.model_validate(deepcopy(admin)).model_dump()

    await session.delete(admin)
    await session.commit()
    
    logger.info(f"Admin deleted: {admin_id} by super admin {current_admin.email}")

    await audit_service.log_action(
        session=session, action="DELETE", table_name="admins",
        record_id=admin_id, admin_id=current_admin.id,
        old_values=old_admin_data
    )
    
    return

# Other endpoints like list, get, stats, etc. remain unchanged as they are read-only.