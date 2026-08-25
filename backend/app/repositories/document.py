from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from app.models.document import Document
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    def __init__(self, db):
        super().__init__(Document, db)

    async def get_by_user_with_dept_filter(self, user_id: int, department_ids: list[int], skip: int = 0, limit: int = 100) -> list[Document]:
        """Get documents uploaded by user, filtered to their department."""
        if not department_ids:
            return []
        result = await self.db.execute(
            select(Document)
            .where(Document.uploaded_by == user_id)
            .where(Document.department_id.in_(department_ids))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_department(self, department_id: int, skip: int = 0, limit: int = 100) -> list[Document]:
        result = await self.db.execute(
            select(Document).where(Document.department_id == department_id).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_with_chunks(self, id: int) -> Document | None:
        result = await self.db.execute(select(Document).options(joinedload(Document.chunks)).where(Document.id == id))
        return result.scalar_one_or_none()

    async def count_by_status(self) -> dict:
        from sqlalchemy import func

        result = await self.db.execute(select(Document.status, func.count()).group_by(Document.status))
        return {row[0].value if hasattr(row[0], "value") else row[0]: row[1] for row in result.all()}