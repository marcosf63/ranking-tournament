
"""
Testes unitários para serviços
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from app.services.ranking_service import RankingService
from app.services.notification_service import NotificationService, NotificationType
from app.services.audit_service import AuditService
from app.models.audit_log import AuditLog


class TestRankingService:
    """Testes para o serviço de ranking"""
    
    def test_ranking_service_initialization(self):
        service = RankingService()
        assert service._general_ranking_cache is None
        assert service._tournament_rankings_cache == {}
        assert service._cache_timestamp is None
        assert service._cache_ttl == 300


class TestNotificationService:
    """Testes para o serviço de notificações"""
    
    def test_notification_service_initialization(self):
        service = NotificationService()
        assert service.email_enabled is False
        assert service._recent_notifications == []
        assert service._max_recent == 100


@pytest.mark.asyncio
class TestAuditService:
    """Testes para o serviço de auditoria"""
    
    async def test_log_action_creation(self, session, test_admin):
        """Testar criação de log de auditoria"""
        audit_log = await audit_service.log_action(
            session=session,
            action="CREATE",
            table_name="player",
            record_id=1,
            admin_id=test_admin.id,
            new_values={"name": "Test Player"}
        )
        
        assert isinstance(audit_log, AuditLog)
        assert audit_log.action == "CREATE"
        assert audit_log.table_name == "player"
        assert audit_log.admin_id == test_admin.id
        assert audit_log.new_values["name"] == "Test Player"

    async def test_get_audit_logs(self, session, test_admin):
        """Testar busca de logs de auditoria"""
        await audit_service.log_action(session, "CREATE", "player", 1, test_admin.id)
        await audit_service.log_action(session, "UPDATE", "player", 1, test_admin.id)
        await audit_service.log_action(session, "CREATE", "tournament", 2, test_admin.id)
        
        all_logs = await audit_service.get_audit_logs(session)
        assert len(all_logs) == 3
        
        player_logs = await audit_service.get_audit_logs(session, table_name="player")
        assert len(player_logs) == 2
        
        resource_logs = await audit_service.get_audit_logs(session, record_id=1)
        assert len(resource_logs) == 2
