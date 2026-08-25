from sqlalchemy import desc, func, select

from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, db):
        super().__init__(AuditLog, db)

    async def list_recent(self, skip: int = 0, limit: int = 100) -> list[AuditLog]:
        result = await self.db.execute(
            select(AuditLog).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count_errors(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(AuditLog).where(AuditLog.success == 0))
        return result.scalar()
