from types import SimpleNamespace

import numpy as np

from src.xictek_website_assistant import service
from src.xictek_website_assistant.schemas import XictekChatRequest
from src.xictek_website_assistant.service_queries import is_portfolio_query
from src.xictek_website_assistant.vector_store import Chunk, VectorStore


PORTFOLIO_URL = "https://xicteksystems.com/portfolio"
PORTFOLIO_TITLE = "Our Work | XICTEK Systems"


def _match(url=PORTFOLIO_URL, title=PORTFOLIO_TITLE, text="HisabDo is an offline-first digital ledger."):
    chunk = Chunk("portfolio-1", title, text, url)
    return SimpleNamespace(chunk=chunk, score=0.71)


def _request(message="What technologies are used to build HisabDo?"):
    return XictekChatRequest(message=message, conversation_id="portfolio-test")


class _FakeStore:
    def __init__(self, matches):
        self.matches = matches
        self.query_args = None

    def __len__(self):
        return 1

    def query(self, vector, **kwargs):
        self.query_args = kwargs
        return self.matches


def test_portfolio_intents_are_detected_without_routing_careers_questions():
    assert is_portfolio_query("What is in your portfolio?")
    assert is_portfolio_query("Which technologies are used to build HisabDo?")
    assert not is_portfolio_query("Which internship roles are open?")


def test_vector_store_portfolio_filter_limits_sources_to_xictek_portfolio_page():
    chunks = [
        Chunk("p1", PORTFOLIO_TITLE, "portfolio", PORTFOLIO_URL),
        Chunk("p2", "Portfolio", "untrusted host", "https://example.com/portfolio"),
        Chunk("p3", "Portfolio", "other XICTEK page", "https://xicteksystems.com/services"),
        Chunk("p4", "Product", "HisabDo product", "https://hisabdo.app/"),
    ]
    store = VectorStore()
    store.build(chunks, np.array([[1.0], [0.99], [0.98], [0.97]], dtype=np.float32))

    results = store.query(
        np.array([1.0], dtype=np.float32), top_k=5, relevance_threshold=0.0,
        diversify=False, url_path_prefix="/portfolio", url_host="xicteksystems.com",
    )

    assert [item.chunk.chunk_id for item in results] == ["p1"]


def test_portfolio_chat_uses_portfolio_filter_and_requires_exact_inline_source_link(monkeypatch):
    store = _FakeStore([_match()])
    captured = {}

    class Provider:
        def generate_reply(self, message, context, history):
            captured["context"] = context
            return f"The retrieved case study says HisabDo uses Flutter. [{PORTFOLIO_TITLE}]({PORTFOLIO_URL})", 12

    monkeypatch.setattr(service, "_load_store", lambda: store)
    monkeypatch.setattr(service, "embed_query", lambda message: np.array([1.0]))
    monkeypatch.setattr(service, "get_llm_provider", lambda: Provider())

    result = service.handle_chat(_request())

    assert store.query_args["url_path_prefix"] == "/portfolio"
    assert store.query_args["url_host"] == "xicteksystems.com"
    assert "Source [1]" in captured["context"]
    assert result.reply.endswith(f"[{PORTFOLIO_TITLE}]({PORTFOLIO_URL})")
    assert result.sources[0].title == PORTFOLIO_TITLE


def test_portfolio_uncited_or_wrong_source_link_returns_grounded_fallback(monkeypatch):
    store = _FakeStore([_match()])

    class Provider:
        def generate_reply(self, message, context, history):
            return "HisabDo reduced costs by 40%. [Case Study](https://example.com/case-study)", 9

    monkeypatch.setattr(service, "_load_store", lambda: store)
    monkeypatch.setattr(service, "embed_query", lambda message: np.array([1.0]))
    monkeypatch.setattr(service, "get_llm_provider", lambda: Provider())

    result = service.handle_chat(_request("What measurable client result did HisabDo deliver?"))

    assert "couldn't verify" in result.reply
    assert result.sources[0].url == PORTFOLIO_URL
    assert "40%" not in result.reply


def test_portfolio_without_matches_does_not_call_llm_and_returns_official_source_fallback(monkeypatch):
    store = _FakeStore([])

    class Provider:
        def generate_reply(self, *args, **kwargs):
            raise AssertionError("Portfolio answers require retrieved evidence")

    monkeypatch.setattr(service, "_load_store", lambda: store)
    monkeypatch.setattr(service, "embed_query", lambda message: np.array([1.0]))
    monkeypatch.setattr(service, "get_llm_provider", lambda: Provider())

    result = service.handle_chat(_request("Tell me about your client case studies"))

    assert "couldn't verify" in result.reply
    assert result.sources[0].url == PORTFOLIO_URL
