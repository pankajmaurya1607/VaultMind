from pydantic import BaseModel
from datetime import datetime
from typing import Optional


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
