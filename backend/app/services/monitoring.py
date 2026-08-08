from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.audit import AuditLogRepository
from app.repositories.chat import MessageRepository
from app.repositories.document import DocumentRepository
from app.repositories.user import UserRepository


class MonitoringService:
    def __init__(self, db: AsyncSession):
        self.doc_repo = DocumentRepository(db)
        self.msg_repo = MessageRepository(db)
        self.audit_repo = AuditLogRepository(db)
        self.user_repo = UserRepository(db)

    async def get_metrics(self) -> dict:
        docs = await self.doc_repo.list()
        doc_status = await self.doc_repo.count_by_status()
        total_tokens = await self.msg_repo.count_tokens()
        avg_latency = await self.msg_repo.avg_latency()
        errors = await self.audit_repo.count_errors()
        users = await self.user_repo.count()

        return {
            "total_documents": len(docs),
            "total_users": users,
            "total_chat_sessions": 0,
            "documents_by_status": doc_status,
            "total_tokens_used": total_tokens,
            "avg_chat_latency_ms": avg_latency,
            "avg_search_latency_ms": 0.0,
            "error_count": errors,
        }
