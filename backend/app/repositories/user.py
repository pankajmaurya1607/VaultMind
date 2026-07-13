from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.repositories.base import BaseRepository
from app.models.user import User
from app.models.role import Role
from app.models.department import Department


class UserRepository(BaseRepository[User]):
    def __init__(self, db):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_with_relations(self, id: int) -> User | None:
        result = await self.db.execute(
            select(User)
            .options(joinedload(User.role), joinedload(User.department))
            .where(User.id == id)
        )
        return result.scalar_one_or_none()

    async def list_with_relations(self, skip: int = 0, limit: int = 100) -> list[User]:
        result = await self.db.execute(
            select(User)
            .options(joinedload(User.role), joinedload(User.department))
            .offset(skip).limit(limit)
        )
        return list(result.unique().scalars().all())
