from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.chat import ChatService


class TestChatService:
    def setup_method(self):
        self.db = AsyncMock()
        self.service = ChatService(self.db)
        self.service.session_repo = AsyncMock()
        self.service.message_repo = AsyncMock()
        self.service.document_repo = AsyncMock()

    @pytest.mark.asyncio
    async def test_chat_creates_session_and_persists_messages(self):
        session = MagicMock(id=10, user_id=1, title="test")
        self.service.session_repo.create = AsyncMock(return_value=session)
        self.service.retriever.search = AsyncMock(
            return_value=[{"document_id": 1, "filename": "p.txt", "chunk_index": 0, "text": "x", "score": 0.9}]
        )
        self.service.generator.generate = MagicMock(
            return_value=(
                "Answer here",
                [{"document_id": 1, "filename": "p.txt", "chunk_index": 0, "text": "x", "score": 0.9}],
                0.9,
            )
        )

        result = await self.service.chat("What is policy?", user_id=1, department_ids=[2])

        assert result["session_id"] == 10
        assert result["answer"] == "Answer here"
        assert result["sources"][0]["document_id"] == 1
        assert result["confidence_score"] == 0.9
        assert self.service.message_repo.create.await_count == 2

    @pytest.mark.asyncio
    async def test_chat_reuses_own_session(self):
        session = MagicMock(id=7, user_id=1, title="existing")
        self.service.session_repo.get_with_messages = AsyncMock(return_value=session)
        self.service.retriever.search = AsyncMock(return_value=[])
        self.service.generator.generate = MagicMock(return_value=("no info", [], 0.0))

        result = await self.service.chat("q", user_id=1, department_ids=[2], session_id=7)

        assert result["session_id"] == 7
        self.service.session_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_chat_ignores_foreign_session(self):
        foreign = MagicMock(id=7, user_id=999, title="other")
        created = MagicMock(id=8, user_id=1, title="new")
        self.service.session_repo.get_with_messages = AsyncMock(return_value=foreign)
        self.service.session_repo.create = AsyncMock(return_value=created)
        self.service.retriever.search = AsyncMock(return_value=[])
        self.service.generator.generate = MagicMock(return_value=("no info", [], 0.0))

        result = await self.service.chat("q", user_id=1, department_ids=[2], session_id=7)

        assert result["session_id"] == 8
        self.service.session_repo.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_messages_denies_foreign_session(self):
        foreign = MagicMock(id=5, user_id=999)
        self.service.session_repo.get = AsyncMock(return_value=foreign)
        result = await self.service.get_messages(5, user_id=1)
        assert result == []
