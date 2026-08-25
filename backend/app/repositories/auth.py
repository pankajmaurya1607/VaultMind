from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

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

    async def prune_expired(self, max_age_days: int) -> int:
        """Delete blacklist entries older than the longest token lifetime.

        After max_age_days every token carrying that jti has expired anyway,
        so the row no longer serves a security purpose.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        result = await self.db.execute(delete(BlacklistedToken).where(BlacklistedToken.created_at < cutoff))
        return result.rowcount or 0
