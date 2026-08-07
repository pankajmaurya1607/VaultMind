from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.blacklisted_token import BlacklistedToken


class AuthRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def blacklist_token(self, jti: str) -> None:
        existing = await self.db.execute(select(BlacklistedToken).where(BlacklistedToken.jti == jti))
        if existing.scalar_one_or_none() is None:
            self.db.add(BlacklistedToken(jti=jti))

    async def is_blacklisted(self, jti: str) -> bool:
        result = await self.db.execute(select(BlacklistedToken).where(BlacklistedToken.jti == jti))
        return result.scalar_one_or_none() is not None
