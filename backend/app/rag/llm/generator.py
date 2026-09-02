import logging
from typing import List

from app.config.settings import settings
from app.monitoring.metrics import TOKENS_USED

logger = logging.getLogger("eka")

SYSTEM_PROMPT = """You are an enterprise knowledge assistant. Your purpose is to help employees find answers from
company documents.

CRITICAL RULES:
1. Answer ONLY using the provided context documents.
2. If the context is insufficient to answer the question, say "I don't have enough information to answer this question."
3. NEVER fabricate or hallucinate information.
4. NEVER reveal the existence of hidden or restricted documents.
5. ALWAYS cite your sources by referencing the document filename.
6. Be concise and professional.
7. If the question is not related to the knowledge base, politely decline to answer.

RESPONSE STYLE - Make answers beautiful, clear and engaging:
- Start with a brief 1-line summary with an emoji (e.g., 🌍, 💼, 📊, 🛡️, 💡)
- Use clear markdown headings with emojis: ## 🌍 Purpose, ## ✨ Key Features, ## 👥 Stakeholders, ## 💰 Benefits, ## 🔄 Stages, etc.
- For lists, use bullet points with emojis (• → use - with emoji prefix like - 🌟, - 📌)
- For comparisons or structured data, use a markdown table with an emoji in the header (e.g., | Topic | Summary |)
- Keep tables compact (max 4 columns, short cells)
- End with a helpful 1-line invite: "Want to dive deeper into X? Let me know! 💬"
- Always keep it scannable, not wall-of-text. Use bold for key terms.
- Cite sources inline as [filename] after each section."""

try:
    from langchain_google_genai import ChatGoogleGenerativeAI

    _gemini_available = bool(settings.GEMINI_API_KEY)
except Exception:
    _gemini_available = False

try:
    from langchain_groq import ChatGroq

    _groq_available = bool(settings.GROQ_API_KEY)
except Exception:
    _groq_available = False


class Generator:
    def __init__(self):
        self._llm = None
        self.last_tokens = 0
        self.model_name = "template"
        self.model_provider = "fallback"

        if _gemini_available:
            try:
                self._llm = ChatGoogleGenerativeAI(
                    model=settings.GEMINI_CHAT_MODEL,
                    google_api_key=settings.GEMINI_API_KEY,
                    temperature=0.1,
                )
                self.model_name = settings.GEMINI_CHAT_MODEL
                self.model_provider = "gemini"
                logger.info(f"Using Gemini: {settings.GEMINI_CHAT_MODEL}")
            except Exception as e:
                logger.warning(f"Gemini init failed: {e}")

        if self._llm is None and _groq_available:
            try:
                self._llm = ChatGroq(
                    model=settings.GROQ_MODEL,
                    groq_api_key=settings.GROQ_API_KEY,
                    temperature=0.1,
                )
                self.model_name = settings.GROQ_MODEL
                self.model_provider = "groq"
                logger.info(f"Using Groq: {settings.GROQ_MODEL}")
            except Exception as e:
                logger.warning(f"Groq init failed: {e}")

        if self._llm is None:
            self.model_name = "template"
            self.model_provider = "fallback"
            logger.warning("No LLM available, using fallback response (template)")

    def generate(self, question: str, documents: List[dict]) -> tuple:
        if not documents:
            return "I don't have enough information to answer this question.", [], 0.0

        context = self._format_context(documents)
        sources = [
            {
                "document_id": d["document_id"],
                "filename": d["filename"],
                "chunk_index": d["chunk_index"],
                "text": d["text"],
                "score": d["score"],
            }
            for d in documents
        ]

        avg_score = sum(d["score"] for d in documents) / len(documents)

        if self._llm is None:
            return self._fallback_response(question, documents), sources, avg_score

        try:
            from langchain_core.messages import HumanMessage, SystemMessage

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
            TOKENS_USED.labels(model=settings.GEMINI_CHAT_MODEL).inc(tokens)
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
        """Beautiful fallback when no LLM is configured - mimics LLM style with emojis."""
        if not documents:
            return "I don't have enough information to answer this question."

        seen = set()
        cleaned_docs = []
        for d in documents[:3]:
            txt = d["text"].strip().replace("\x00", " ")
            txt = " ".join(txt.split())
            if len(txt) > 320:
                cut = txt[:320]
                last_period = cut.rfind(". ")
                if last_period > 180:
                    txt = cut[: last_period + 1]
                else:
                    txt = cut + "…"
            key = txt[:80]
            if key not in seen:
                seen.add(key)
                cleaned_docs.append({**d, "text": txt})

        q_lower = question.lower()
        # Pick an emoji based on question
        if any(w in q_lower for w in ["trade", "finance"]):
            emoji, title = "💼", "Trade Finance — Key Insights"
        elif any(w in q_lower for w in ["risk"]):
            emoji, title = "🛡️", "Risk in Trade Finance"
        elif any(w in q_lower for w in ["export", "insurance"]):
            emoji, title = "📦", "Export Credit & Insurance"
        else:
            emoji, title = "💡", "Answer"

        lines = []
        lines.append(f"## {emoji} {title}\n")
        lines.append(f"Based on your documents, here's a clear summary:\n")
        for idx, doc in enumerate(cleaned_docs, 1):
            lines.append(f"**{idx}. 📄 {doc['filename']}** — {doc['text']}  [{idx}]")
            lines.append("")

        # Add a quick table-like summary if multiple docs
        if len(cleaned_docs) > 1:
            lines.append("**✨ At a glance:**")
            for doc in cleaned_docs:
                lines.append(f"- 🌟 {doc['text'][:90]}…")
            lines.append("")

        lines.append("Want to dive deeper into a specific aspect? Let me know! 💬")

        max_score = max(d["score"] for d in documents) if documents else 0
        avg_score = sum(d["score"] for d in documents) / len(documents) if documents else 0
        if max_score > 0.05:
            lines.append(f"\n*Relevance: {avg_score*100:.0f}% · Sources: {len(cleaned_docs)} · Model: template fallback*")
        else:
            lines.append(f"\n*Sources: {len(cleaned_docs)} · Model: template fallback*")

        return "\n".join(lines).strip()
