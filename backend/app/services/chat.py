import asyncio
import logging
import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_session import ChatSession
from app.monitoring.metrics import CHAT_LATENCY, LLM_LATENCY, record_search_latency
from app.rag.llm.generator import Generator
from app.rag.retriever.retriever import Retriever
from app.repositories.chat import ChatSessionRepository, MessageRepository
from app.repositories.document import DocumentRepository

logger = logging.getLogger("eka")


class ChatService:
    def __init__(self, db: AsyncSession):
        self.session_repo = ChatSessionRepository(db)
        self.message_repo = MessageRepository(db)
        self.document_repo = DocumentRepository(db)
        self.retriever = Retriever()
        self.generator = Generator()
        self.db = db

    def _generate_title(self, question: str) -> str:
        q = " ".join(question.strip().split())
        if not q:
            return "New Chat"
        # Use first sentence for meaningful title
        for sep in ["?", ".", "!", "\n"]:
            if sep in q:
                q = q.split(sep)[0].strip()
                break
        q = q[:60].strip()
        if len(question.strip()) > len(q):
            # avoid cutting mid-word
            if len(q) == 60 and " " in q:
                q = q.rsplit(" ", 1)[0]
            q += "…"
        return q[0].upper() + q[1:] if len(q) > 1 else q.upper()

    async def chat(self, question: str, user_id: int, department_ids: list[int], session_id: int | None = None) -> dict:
        if session_id:
            session = await self.session_repo.get_with_messages(session_id)
            if not session or session.user_id != user_id:
                session = await self.session_repo.create(user_id=user_id, title=self._generate_title(question))
        else:
            session = await self.session_repo.create(user_id=user_id, title=self._generate_title(question))

        search_start = time.time()
        documents = await self.retriever.search(question, department_ids, db=self.db)
        search_time = (time.time() - search_start) * 1000
        record_search_latency(search_time)

        llm_start = time.time()
        # Sync LLM SDK call - offload so the event loop isn't blocked.
        answer, sources, confidence = await asyncio.to_thread(self.generator.generate, question, documents)
        llm_time = (time.time() - llm_start) * 1000
        LLM_LATENCY.observe(llm_time)
        CHAT_LATENCY.observe(search_time + llm_time)

        source_data = [
            {
                "document_id": s["document_id"],
                "filename": s["filename"],
                "chunk_index": s["chunk_index"],
                "text": s["text"],
                "score": s["score"],
            }
            for s in sources
        ]

        await self.message_repo.create(
            session_id=session.id,
            role="user",
            content=question,
        )

        await self.message_repo.create(
            session_id=session.id,
            role="assistant",
            content=answer,
            sources=source_data,
            confidence_score=confidence,
            tokens_used=self.generator.last_tokens,
            latency_ms=int(search_time + llm_time),
        )

        return {
            "session_id": session.id,
            "answer": answer,
            "sources": source_data,
            "confidence_score": confidence,
            "tokens_used": self.generator.last_tokens,
            "latency_ms": int(search_time + llm_time),
            "model": getattr(self.generator, "model_name", "template"),
            "model_provider": getattr(self.generator, "model_provider", "fallback"),
        }

    async def search(self, query: str, department_ids: list[int], top_k: int = 5) -> list[dict]:
        search_start = time.time()
        results = await self.retriever.search(query, department_ids, top_k, db=self.db)
        search_time = (time.time() - search_start) * 1000
        record_search_latency(search_time)
        return results

    async def get_history(self, user_id: int) -> list[ChatSession]:
        sessions = await self.session_repo.get_by_user(user_id)
        return sessions

    async def get_history_with_counts(self, user_id: int) -> list[tuple[ChatSession, int]]:
        return await self.session_repo.get_by_user_with_message_counts(user_id)

    async def get_messages(self, session_id: int, user_id: int) -> list:
        session = await self.session_repo.get(session_id)
        if not session or session.user_id != user_id:
            return []
        return await self.message_repo.get_by_session(session_id)

    async def rename_session(self, session_id: int, user_id: int, new_title: str) -> ChatSession | None:
        session = await self.session_repo.get(session_id)
        if not session or session.user_id != user_id:
            return None
        title = " ".join(new_title.strip().split())[:80]
        if not title:
            return None
        return await self.session_repo.update(session_id, title=title)

    async def delete_session(self, session_id: int, user_id: int) -> bool:
        session = await self.session_repo.get(session_id)
        if not session or session.user_id != user_id:
            return False
        return await self.session_repo.delete(session_id)
