from sqlalchemy.ext.asyncio import AsyncSession

from app.monitoring.metrics import search_latency_stats
from app.repositories.audit import AuditLogRepository
from app.repositories.chat import ChatSessionRepository, MessageRepository
from app.repositories.document import DocumentRepository
from app.repositories.user import UserRepository


class MonitoringService:
    def __init__(self, db: AsyncSession):
        self.doc_repo = DocumentRepository(db)
        self.msg_repo = MessageRepository(db)
        self.session_repo = ChatSessionRepository(db)
        self.audit_repo = AuditLogRepository(db)
        self.user_repo = UserRepository(db)

    async def get_metrics(self) -> dict:
        docs = await self.doc_repo.list()
        doc_status = await self.doc_repo.count_by_status()
        total_tokens = await self.msg_repo.count_tokens()
        avg_latency = await self.msg_repo.avg_latency()
        errors = await self.audit_repo.count_errors()
        users = await self.user_repo.count()
        chat_sessions = await self.session_repo.count()

        avg_search, _ = search_latency_stats()

        return {
            "total_documents": len(docs),
            "total_users": users,
            "total_chat_sessions": chat_sessions,
            "documents_by_status": doc_status,
            "total_tokens_used": total_tokens,
            "avg_chat_latency_ms": round(avg_latency, 2),
            "avg_search_latency_ms": avg_search,
            "error_count": errors,
        }
