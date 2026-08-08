from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: Optional[int] = None
    question: str


class Source(BaseModel):
    document_id: int
    filename: str
    chunk_index: int
    text: str
    score: float


class ChatResponse(BaseModel):
    session_id: int
    answer: str
    sources: List[Source]
    confidence_score: float
    tokens_used: int
    latency_ms: int


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    document_id: int
    filename: str
    chunk_index: int
    text: str
    score: float
    metadata: dict


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int


class ChatHistoryResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    message_count: int

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    sources: Optional[List[Source]] = None
    confidence_score: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}
