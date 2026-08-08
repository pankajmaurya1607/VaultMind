from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: int
    user_email: Optional[str] = None
    action: str
    resource: str
    details: Optional[str] = None
    ip_address: Optional[str] = None
    success: int
    created_at: datetime

    model_config = {"from_attributes": True}
