from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    action: str
    resource: str
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
