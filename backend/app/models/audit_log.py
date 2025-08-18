from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON
from typing import Optional, Dict, Any
from datetime import datetime


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"
    
    id: Optional[int] = Field(primary_key=True)
    table_name: str = Field(max_length=50, nullable=False, index=True)
    record_id: int = Field(nullable=False, index=True)
    action: str = Field(max_length=10, nullable=False)
    old_values: Optional[Dict[str, Any]] = Field(sa_column=Column(JSON), default=None)
    new_values: Optional[Dict[str, Any]] = Field(sa_column=Column(JSON), default=None)
    admin_id: int = Field(foreign_key="admins.id", nullable=False)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)