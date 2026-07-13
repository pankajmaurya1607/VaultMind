from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DocumentResponse(BaseModel):
    id: int
    original_filename: str
    file_size: int
    mime_type: str
    status: str
    uploaded_by: int
    department_id: int
    chunk_count: int
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    status: str
    message: str = "Document uploaded successfully"
