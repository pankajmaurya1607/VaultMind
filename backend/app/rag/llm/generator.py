import logging
from typing import List
from app.config.settings import settings
from app.monitoring.metrics import TOKENS_USED

logger = logging.getLogger("eka")

SYSTEM_PROMPT = """You are an enterprise knowledge assistant. Your purpose is to help employees find answers from company documents.

CRITICAL RULES:
1. Answer ONLY using the provided context documents.
2. If the context is insufficient to answer the question, say "I don't have enough information to answer this question."
3. NEVER fabricate or hallucinate information.
4. NEVER reveal the existence of hidden or restricted documents.
5. ALWAYS cite your sources by referencing the document filename.
6. Be concise and professional.
7. If the question is not related to the knowledge base, politely decline to answer."""

try:
    from langchain_openai import ChatOpenAI
    _openai_available = bool(settings.OPENAI_API_KEY)
except Exception:
    _openai_available = False

try:
    from langchain_groq import ChatGroq
    _groq_available = bool(settings.GROQ_API_KEY)
except Exception:
    _groq_available = False


class Generator:
    def __init__(self):
        self._llm = None
        self.last_tokens = 0

        if _openai_available:
            try:
                self._llm = ChatOpenAI(
                    model=settings.OPENAI_CHAT_MODEL,
                    openai_api_key=settings.OPENAI_API_KEY,
                    temperature=0.1,
                )
                logger.info(f"Using OpenAI: {settings.OPENAI_CHAT_MODEL}")
            except Exception as e:
                logger.warning(f"OpenAI init failed: {e}")

        if self._llm is None and _groq_available:
            try:
                self._llm = ChatGroq(
                    model=settings.GROQ_MODEL,
                    groq_api_key=settings.GROQ_API_KEY,
                    temperature=0.1,
                )
                logger.info(f"Using Groq: {settings.GROQ_MODEL}")
            except Exception as e:
                logger.warning(f"Groq init failed: {e}")

        if self._llm is None:
            logger.warning("No LLM available, using fallback response")

    def generate(self, question: str, documents: List[dict]) -> tuple:
        if not documents:
            return "I don't have enough information to answer this question.", [], 0.0

        context = self._format_context(documents)
        sources = [{
            "document_id": d["document_id"],
            "filename": d["filename"],
            "chunk_index": d["chunk_index"],
            "text": d["text"],
            "score": d["score"],
        } for d in documents]

        avg_score = sum(d["score"] for d in documents) / len(documents)

        if self._llm is None:
            return self._fallback_response(question, documents), sources, avg_score

        try:
            from langchain.schema import HumanMessage, SystemMessage

            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=f"Context:\n{context}\n\nQuestion: {question}"),
            ]

            response = self._llm.invoke(messages)
            tokens = 0
            if hasattr(response, "usage_metadata"):
                tokens = response.usage_metadata.get("total_tokens", 0)
            elif hasattr(response, "response_metadata"):
                tokens = response.response_metadata.get("token_usage", {}).get("total_tokens", 0)

            self.last_tokens = tokens
            TOKENS_USED.labels(model=settings.OPENAI_CHAT_MODEL).inc(tokens)
            return response.content, sources, avg_score

        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            return self._fallback_response(question, documents), sources, avg_score

    def _format_context(self, documents: List[dict]) -> str:
        parts = []
        for i, doc in enumerate(documents, 1):
            parts.append(f"[Source {i}] Filename: {doc['filename']}\nContent: {doc['text']}\n")
        return "\n---\n".join(parts)

    def _fallback_response(self, question: str, documents: List[dict]) -> str:
        parts = [f"Based on the available documents, here is what I found:\n"]
        for doc in documents[:3]:
            parts.append(f"- From '{doc['filename']}': {doc['text'][:200]}...")
        parts.append(f"\nConfidence: {documents[0]['score']:.2f}" if documents else "")
        return "\n".join(parts)
