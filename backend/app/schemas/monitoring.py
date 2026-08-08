from pydantic import BaseModel


class SystemMetrics(BaseModel):
    total_documents: int
    total_users: int
    total_chat_sessions: int
    documents_by_status: dict
    total_tokens_used: int
    avg_chat_latency_ms: float
    avg_search_latency_ms: float
    error_count: int
