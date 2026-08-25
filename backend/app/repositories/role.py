from sqlalchemy import select

from app.models.role import Role
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    def __init__(self, db):
        super().__init__(Role, db)

    async def list(self, skip: int = 0, limit: int = 100) -> list[Role]:
        result = await self.db.execute(
            select(Role).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(Role))
        return result.scalar()