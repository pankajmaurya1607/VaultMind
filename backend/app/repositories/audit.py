from sqlalchemy import desc, select

from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, db):
        super().__init__(AuditLog, db)

    async def list_recent(self, limit: int = 100) -> list[AuditLog]:
        result = await self.db.execute(select(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit))
        return list(result.scalars().all())

    async def count_errors(self) -> int:
        result = await self.db.execute(select(AuditLog).where(AuditLog.action == "error"))
        return len(result.scalars().all())
