from sqlalchemy import desc, func, select
from sqlalchemy.orm import joinedload

from app.models.chat_session import ChatSession
from app.models.message import Message
from app.repositories.base import BaseRepository


class ChatSessionRepository(BaseRepository[ChatSession]):
    def __init__(self, db):
        super().__init__(ChatSession, db)

    async def get_by_user(self, user_id: int, skip: int = 0, limit: int = 50) -> list[ChatSession]:
        result = await self.db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(desc(ChatSession.updated_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_user_with_message_counts(
        self, user_id: int, skip: int = 0, limit: int = 50
    ) -> list[tuple[ChatSession, int]]:
        """Sessions ordered by recency with per-session message counts
        computed in SQL (avoids loading every message just to count it)."""
        message_count = (
            select(func.count(Message.id))
            .where(Message.session_id == ChatSession.id)
            .correlate(ChatSession)
            .scalar_subquery()
        )
        result = await self.db.execute(
            select(ChatSession, message_count)
            .where(ChatSession.user_id == user_id)
            .order_by(desc(ChatSession.updated_at))
            .offset(skip)
            .limit(limit)
        )
        return [(session, count or 0) for session, count in result.all()]

    async def get_with_messages(self, id: int) -> ChatSession | None:
        result = await self.db.execute(
            select(ChatSession).options(joinedload(ChatSession.messages)).where(ChatSession.id == id)
        )
        return result.unique().scalar_one_or_none()


class MessageRepository(BaseRepository[Message]):
    def __init__(self, db):
        super().__init__(Message, db)

    async def get_by_session(self, session_id: int) -> list[Message]:
        result = await self.db.execute(
            select(Message).where(Message.session_id == session_id).order_by(Message.created_at)
        )
        return list(result.scalars().all())

    async def count_tokens(self) -> int:
        result = await self.db.execute(select(func.coalesce(func.sum(Message.tokens_used), 0)))
        return result.scalar()

    async def avg_latency(self) -> float:
        result = await self.db.execute(select(func.avg(Message.latency_ms)))
        return result.scalar() or 0.0
