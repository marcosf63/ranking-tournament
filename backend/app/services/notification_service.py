
"""
Serviço de notificações para eventos importantes do sistema
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from enum import Enum
import logging
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

from ..models.admin import Admin
from ..models.player import Player
from ..models.tournament import Tournament
from ..models.score import Score

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    TOURNAMENT_CREATED = "tournament_created"
    TOURNAMENT_STARTED = "tournament_started"
    TOURNAMENT_ENDED = "tournament_ended"
    SCORE_ADDED = "score_added"
    SCORE_UPDATED = "score_updated"
    RANKING_CHANGED = "ranking_changed"
    ADMIN_LOGIN = "admin_login"
    BULK_IMPORT = "bulk_import"
    SYSTEM_ERROR = "system_error"


class NotificationService:
    """Serviço para envio de notificações"""
    
    def __init__(self):
        self.email_enabled = False  # Configurar se email está habilitado
        self.smtp_host = "localhost"
        self.smtp_port = 587
        self.smtp_user = ""
        self.smtp_password = ""
        self.from_email = "noreply@ranking.com"
        
        self._recent_notifications = []
        self._max_recent = 100
    
    async def send_notification(
        self,
        session: AsyncSession,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        admin_ids: Optional[List[int]] = None,
        send_email: bool = False
    ):
        notification = {
            'id': len(self._recent_notifications) + 1,
            'type': notification_type,
            'title': title,
            'message': message,
            'data': data or {},
            'timestamp': datetime.utcnow().isoformat(),
            'admin_ids': admin_ids,
            'read_by': []
        }
        
        self._recent_notifications.append(notification)
        if len(self._recent_notifications) > self._max_recent:
            self._recent_notifications = self._recent_notifications[-self._max_recent:]
        
        logger.info(f"Notification sent: {notification_type} - {title}")
        
        if send_email and self.email_enabled:
            await self._send_email_notification(session, notification, admin_ids)
        
        return notification
    
    async def _send_email_notification(self, session: AsyncSession, notification: Dict, admin_ids: Optional[List[int]]):
        if not self.email_enabled:
            return
        
        try:
            query = select(Admin).where(Admin.is_active == True)
            if admin_ids:
                query = query.where(Admin.id.in_(admin_ids))
            
            result = await session.exec(query)
            admins = result.all()
            
            for admin in admins:
                if admin.email:
                    self._send_email(
                        to_email=admin.email,
                        subject=notification['title'],
                        body=notification['message']
                    )
        except Exception as e:
            logger.error(f"Error sending email notifications: {e}")

    def _send_email(self, to_email: str, subject: str, body: str):
        """(Sync) Enviar email individual"""
        try:
            msg = MimeMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MimeText(body, 'plain'))
            
            # Esta parte é bloqueante e deve ser executada em um thread pool em produção
            # ou substituída por uma biblioteca de envio de email assíncrona.
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            text = msg.as_string()
            server.sendmail(self.from_email, to_email, text)
            server.quit()
            
            logger.info(f"Email sent to {to_email}")
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")

# Instância global do serviço
notification_service = NotificationService()
