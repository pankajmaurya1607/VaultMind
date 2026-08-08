from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.rag.llm.generator import Generator


def make_documents():
    return [
        {
            "document_id": 1,
            "filename": "policy.txt",
            "chunk_index": 0,
            "text": "Our WFH policy allows 2 days.",
            "score": 0.9,
        },
        {
            "document_id": 2,
            "filename": "hr.md",
            "chunk_index": 1,
            "text": "Employees get 20 paid days.",
            "score": 0.8,
        },
    ]


class TestGenerator:
    def test_empty_documents(self):
        gen = Generator()
        answer, sources, confidence = gen.generate("What is the policy?", [])
        assert "enough information" in answer
        assert sources == []
        assert confidence == 0.0

    def test_fallback_response_without_llm(self, monkeypatch):
        gen = Generator()
        monkeypatch.setattr(gen, "_llm", None)
        docs = make_documents()
        answer, sources, confidence = gen.generate("What is the policy?", docs)
        assert "policy.txt" in answer
        assert len(sources) == 2
        assert sources[0]["document_id"] == 1
        assert confidence == pytest.approx(0.85)
        assert gen.last_tokens == 0

    def test_llm_invocation_success(self, monkeypatch):
        gen = Generator()
        fake_llm = MagicMock()
        fake_llm.invoke.return_value = SimpleNamespace(
            content="Two days per week.",
            usage_metadata={"total_tokens": 57},
        )
        monkeypatch.setattr(gen, "_llm", fake_llm)

        answer, sources, _ = gen.generate("What is the policy?", make_documents())
        assert answer == "Two days per week."
        assert gen.last_tokens == 57
        assert len(sources) == 2

    def test_llm_failure_falls_back(self, monkeypatch):
        gen = Generator()
        fake_llm = MagicMock()
        fake_llm.invoke.side_effect = RuntimeError("boom")
        monkeypatch.setattr(gen, "_llm", fake_llm)

        answer, sources, confidence = gen.generate("What is the policy?", make_documents())
        assert "policy.txt" in answer
        assert gen.last_tokens == 0
