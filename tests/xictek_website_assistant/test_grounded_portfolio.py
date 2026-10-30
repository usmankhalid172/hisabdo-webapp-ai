from src.xictek_website_assistant.schemas import XictekChatRequest
from src.xictek_website_assistant.service import handle_chat
from src.xictek_website_assistant.vector_store import Chunk, RetrievedChunk


def test_portfolio_answer_uses_only_portfolio_retrieval_and_cites_it(monkeypatch):
    class Store:
        def __len__(self):
            return 1

        def query(self, query_vector, **kwargs):
            assert kwargs["url_prefix"] == "https://xicteksystems.com/portfolio"
            return [
                RetrievedChunk(
                    Chunk(
                        "portfolio-1",
                        "Our Work | XICTEK Systems",
                        "HisabDo is built with Flutter, Supabase, and PostgreSQL.",
                        "https://xicteksystems.com/portfolio",
                    ),
                    0.82,
                )
            ]

    class Provider:
        def generate_reply(self, message, context, history):
            assert "Flutter, Supabase, and PostgreSQL" in context
            return "HisabDo uses Flutter, Supabase, and PostgreSQL.", 8

    monkeypatch.setattr("src.xictek_website_assistant.service._load_store", lambda: Store())
    monkeypatch.setattr("src.xictek_website_assistant.service.embed_query", lambda message: [1.0])
    monkeypatch.setattr("src.xictek_website_assistant.service.get_llm_provider", lambda: Provider())

    response = handle_chat(
        XictekChatRequest(message="Tell me about the HisabDo case study", conversation_id="case")
    )

    assert response.intent == "answered"
    assert [source.url for source in response.sources] == ["https://xicteksystems.com/portfolio"]


def test_missing_retrieval_returns_no_answer_without_calling_llm(monkeypatch):
    class EmptyStore:
        def __len__(self):
            return 0

    def fail_if_called():
        raise AssertionError("provider must not be called without retrieved evidence")

    monkeypatch.setattr("src.xictek_website_assistant.service._load_store", lambda: EmptyStore())
    monkeypatch.setattr("src.xictek_website_assistant.service.get_llm_provider", fail_if_called)

    response = handle_chat(
        XictekChatRequest(message="What was the client's ROI?", conversation_id="unsupported")
    )

    assert response.intent == "general"
    assert response.sources == []
    assert "verified answer" in response.reply
