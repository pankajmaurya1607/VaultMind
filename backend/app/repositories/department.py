from sqlalchemy import select

from app.models.department import Department
from app.repositories.base import BaseRepository


class DepartmentRepository(BaseRepository[Department]):
    def __init__(self, db):
        super().__init__(Department, db)

    async def list(self, skip: int = 0, limit: int = 100) -> list[Department]:
        result = await self.db.execute(
            select(Department).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(Department))
        return result.scalar()