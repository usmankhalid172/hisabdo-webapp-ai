import json
import sys
from types import SimpleNamespace

from src.financial_assistant.faq_rag import FaqRetriever


def _write_docs(tmp_path):
    docs = [{
        "id": "faq-002",
        "title": "Expense categorization",
        "text": "HisabDo automatically categorizes expenses."
    }]
    path = tmp_path / "faq_docs.json"
    path.write_text(json.dumps(docs), encoding="utf-8")
    return path


def test_initialization_embedding_failure_uses_tfidf_fallback(tmp_path, monkeypatch):
    class FakeEmbeddings:
        def create(self, **kwargs):
            raise RuntimeError("Embedding provider unavailable")

    class FakeOpenAI:
        def __init__(self):
            self.embeddings = FakeEmbeddings()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeOpenAI))

    retriever = FaqRetriever(docs_path=_write_docs(tmp_path))
    results = retriever.retrieve("How do I categorize expenses?")

    assert retriever._client is None
    assert retriever._embeddings is None
    assert results
    assert results[0]["id"] == "faq-002"


def test_query_embedding_failure_returns_no_matches(tmp_path, monkeypatch):
    class FakeEmbeddings:
        def __init__(self):
            self.calls = 0

        def create(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                item = SimpleNamespace(embedding=[1.0, 0.0])
                return SimpleNamespace(data=[item])
            raise RuntimeError("Query provider unavailable")

    class FakeOpenAI:
        def __init__(self):
            self.embeddings = FakeEmbeddings()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeOpenAI))

    retriever = FaqRetriever(docs_path=_write_docs(tmp_path))
    results = retriever.retrieve("How do I categorize expenses?")

    assert results == []
