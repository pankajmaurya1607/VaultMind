import logging
from typing import List

import httpx

from app.config.settings import settings
from app.monitoring.metrics import TOKENS_USED

logger = logging.getLogger("eka")

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
_LLM_TIMEOUT = 60.0

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

_gemini_available = bool(settings.GEMINI_API_KEY)
_groq_available = bool(settings.GROQ_API_KEY)


def _call_gemini(prompt: str) -> tuple[str, int]:
    """Direct Gemini generateContent REST call (no langchain). Returns (text, tokens)."""
    url = f"{GEMINI_API_BASE}/{settings.GEMINI_CHAT_MODEL}:generateContent"
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1},
    }
    resp = httpx.post(
        url,
        headers={"x-goog-api-key": settings.GEMINI_API_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=_LLM_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    candidates = data.get("candidates") or []
    parts = ((candidates[0].get("content") or {}).get("parts") or []) if candidates else []
    text = "".join(p.get("text", "") for p in parts if isinstance(p, dict)).strip()
    if not text:
        raise RuntimeError(f"Gemini returned no text: {str(data)[:200]}")
    tokens = (data.get("usageMetadata") or {}).get("totalTokenCount", 0) or 0
    return text, int(tokens)


def _call_groq(prompt: str) -> tuple[str, int]:
    """Direct Groq OpenAI-compatible chat call (no langchain). Returns (text, tokens)."""
    resp = httpx.post(
        GROQ_API_URL,
        headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": settings.GROQ_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        },
        timeout=_LLM_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    choices = data.get("choices") or []
    text = ((choices[0].get("message") or {}).get("content") or "").strip() if choices else ""
    if not text:
        raise RuntimeError(f"Groq returned no text: {str(data)[:200]}")
    tokens = (data.get("usage") or {}).get("total_tokens", 0) or 0
    return text, int(tokens)


class Generator:
    def __init__(self):
        self.last_tokens = 0
        if _gemini_available:
            self.model_name = settings.GEMINI_CHAT_MODEL
            self.model_provider = "gemini"
            logger.info(f"Using Gemini: {settings.GEMINI_CHAT_MODEL}")
        elif _groq_available:
            self.model_name = settings.GROQ_MODEL
            self.model_provider = "groq"
            logger.info(f"Using Groq: {settings.GROQ_MODEL}")
        else:
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

        if self.model_provider == "fallback":
            return self._fallback_response(question, documents), sources, avg_score

        prompt = f"Context:\n{context}\n\nQuestion: {question}"

        # Failover order: primary provider first, then the other LLM if a key exists.
        # (Module-level _gemini_available/_groq_available are import-time; read
        # settings live so a key added without reimport still gets tried.)
        attempts: list[str] = []
        if self.model_provider == "gemini":
            attempts.append("gemini")
        elif self.model_provider == "groq":
            attempts.append("groq")
        else:
            if settings.GEMINI_API_KEY:
                attempts.append("gemini")
            if settings.GROQ_API_KEY:
                attempts.append("groq")
        if self.model_provider == "gemini" and settings.GROQ_API_KEY and "groq" not in attempts:
            attempts.append("groq")
        if self.model_provider == "groq" and settings.GEMINI_API_KEY and "gemini" not in attempts:
            attempts.append("gemini")

        if not attempts:
            return self._fallback_response(question, documents), sources, avg_score

        model_for = {"gemini": settings.GEMINI_CHAT_MODEL, "groq": settings.GROQ_MODEL}
        last_error: Exception | None = None
        for provider in attempts:
            try:
                if provider == "gemini":
                    content, tokens = _call_gemini(prompt)
                else:
                    content, tokens = _call_groq(prompt)
                self.model_provider = provider
                self.model_name = model_for[provider]
                self.last_tokens = tokens
                TOKENS_USED.labels(model=self.model_name).inc(tokens)
                return content, sources, avg_score
            except Exception as e:
                last_error = e
                logger.error(f"LLM invocation failed ({provider}/{model_for[provider]}): {e}")

        logger.error(f"All LLM providers failed, using fallback. Last error: {last_error}")
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
