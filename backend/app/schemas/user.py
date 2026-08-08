from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    department_id: int
    department_name: Optional[str] = None
    role_id: int
    role_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: Optional[str] = None
    department_id: Optional[int] = None
    role_id: Optional[int] = None
