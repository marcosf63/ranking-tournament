
"""
Serviço de auditoria para registrar todas as ações do sistema
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import datetime, timedelta
import logging
import json

from ..models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """Serviço para registrar logs de auditoria"""
    
    async def log_action(
        self,
        session: AsyncSession,
        action: str,
        table_name: str,
        record_id: Optional[int] = None,
        admin_id: Optional[int] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Registrar uma ação de auditoria
        """
        try:
            audit_log = AuditLog(
                action=action,
                table_name=table_name,
                record_id=record_id,
                admin_id=admin_id,
                old_values=old_values,
                new_values=new_values,
                timestamp=datetime.utcnow()
            )
            
            session.add(audit_log)
            await session.commit()
            await session.refresh(audit_log)
            
            logger.info(f"Audit log created: {action} on {table_name} {record_id} by admin {admin_id}")
            return audit_log
            
        except Exception as e:
            logger.error(f"Error creating audit log: {e}")
            await session.rollback()
            raise
    
    async def get_audit_logs(
        self,
        session: AsyncSession,
        table_name: Optional[str] = None,
        record_id: Optional[int] = None,
        admin_id: Optional[int] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        Buscar logs de auditoria com filtros
        """
        query = select(AuditLog)
        
        if table_name:
            query = query.where(AuditLog.table_name == table_name)
        
        if record_id:
            query = query.where(AuditLog.record_id == record_id)
        
        if admin_id:
            query = query.where(AuditLog.admin_id == admin_id)
        
        if action:
            query = query.where(AuditLog.action == action)
        
        if start_date:
            query = query.where(AuditLog.timestamp >= start_date)
        
        if end_date:
            query = query.where(AuditLog.timestamp <= end_date)
        
        query = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit)
        
        result = await session.exec(query)
        return result.all()

# Instância global do serviço
audit_service = AuditService()
