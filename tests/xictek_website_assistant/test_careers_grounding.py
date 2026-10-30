from types import SimpleNamespace
from pathlib import Path

import numpy as np

from src.xictek_website_assistant import service
from src.xictek_website_assistant.llm_client import MockLLMProvider
from src.xictek_website_assistant.prompts import SYSTEM_PROMPT
from src.xictek_website_assistant.schemas import XictekChatRequest
from src.xictek_website_assistant.service_queries import is_careers_query, is_personal_application_status_query
from src.xictek_website_assistant.vector_store import Chunk, VectorStore


def _request(message="What jobs are open?"):
    return XictekChatRequest(message=message, conversation_id="careers-test")


def _match(url="https://xicteksystems.com/careers", text="A listed role."):
    chunk = Chunk(chunk_id="careers-1", title="Careers | XICTEK Systems", url=url, text=text)
    return SimpleNamespace(chunk=chunk, score=0.75)


class _FakeStore:
    def __init__(self, matches):
        self.matches = matches
        self.query_args = None

    def __len__(self):
        return 1

    def query(self, vector, **kwargs):
        self.query_args = kwargs
        return self.matches


def test_careers_intents_are_detected_without_routing_general_service_questions():
    assert is_careers_query("Which internship roles are available?")
    assert is_careers_query("How do I apply for a job?")
    assert not is_careers_query("What software services do you offer?")


def test_vector_store_careers_filter_keeps_xictek_domain_separate():
    chunks = [
        Chunk("x1", "Careers", "XICTEK role", "https://xicteksystems.com/careers"),
        Chunk("x2", "Internship", "XICTEK internship", "https://www.xicteksystems.com/careers/internship"),
        Chunk("h1", "Careers at HisabDo", "HisabDo role", "https://hisabdo.app/careers"),
        Chunk("s1", "Services", "service", "https://xicteksystems.com/services"),
    ]
    store = VectorStore()
    store.build(chunks, np.array([[1.0], [0.9], [0.99], [0.98]], dtype=np.float32))

    results = store.query(
        np.array([1.0], dtype=np.float32),
        top_k=5,
        relevance_threshold=0.0,
        diversify=False,
        url_path_prefix="/careers",
        url_host="xicteksystems.com",
    )

    assert [item.chunk.chunk_id for item in results] == ["x1", "x2"]


def test_careers_chat_sends_numbered_source_context_and_domain_filter(monkeypatch):
    store = _FakeStore([_match()])
    captured = {}

    class Provider:
        def generate_reply(self, message, context, history):
            captured["context"] = context
            return "The page lists this role [1].", 8

    monkeypatch.setattr(service, "_load_store", lambda: store)
    monkeypatch.setattr(service, "embed_query", lambda message: np.array([1.0]))
    monkeypatch.setattr(service, "get_llm_provider", lambda: Provider())

    result = service.handle_chat(_request())

    assert store.query_args["top_k"] == 4
    assert store.query_args["relevance_threshold"] == 0.12
    assert store.query_args["url_path_prefix"] == "/careers"
    assert store.query_args["url_host"] == "xicteksystems.com"
    assert "Source [1]" in captured["context"]
    assert "URL: https://xicteksystems.com/careers" in captured["context"]
    assert result.sources[0].url == "https://xicteksystems.com/careers"
    assert result.reply.endswith("[1].")


def test_careers_without_retrieved_evidence_returns_linked_fallback(monkeypatch):
    store = _FakeStore([])

    class Provider:
        def generate_reply(self, *args, **kwargs):
            raise AssertionError("The LLM must not answer a Careers question without evidence")

    monkeypatch.setattr(service, "_load_store", lambda: store)
    monkeypatch.setattr(service, "embed_query", lambda message: np.array([1.0]))
    monkeypatch.setattr(service, "get_llm_provider", lambda: Provider())

    result = service.handle_chat(_request("What is the current job application deadline?"))

    assert "couldn't verify" in result.reply
    assert result.reply.endswith("[1].")
    assert result.sources[0].url == service.CAREERS_SOURCE_URL


def test_careers_uncited_or_unknown_citation_falls_back(monkeypatch):
    store = _FakeStore([_match()])

    class Provider:
        def generate_reply(self, message, context, history):
            return "The role is open now.", 5

    monkeypatch.setattr(service, "_load_store", lambda: store)
    monkeypatch.setattr(service, "embed_query", lambda message: np.array([1.0]))
    monkeypatch.setattr(service, "get_llm_provider", lambda: Provider())

    result = service.handle_chat(_request())

    assert "couldn't verify" in result.reply
    assert result.sources[0].url == service.CAREERS_SOURCE_URL


def test_careers_invalid_citation_number_falls_back(monkeypatch):
    store = _FakeStore([_match()])

    class Provider:
        def generate_reply(self, message, context, history):
            return "The role is open [2].", 5

    monkeypatch.setattr(service, "_load_store", lambda: store)
    monkeypatch.setattr(service, "embed_query", lambda message: np.array([1.0]))
    monkeypatch.setattr(service, "get_llm_provider", lambda: Provider())

    result = service.handle_chat(_request())

    assert "couldn't verify" in result.reply
    assert result.sources[0].url == service.CAREERS_SOURCE_URL


def test_system_prompt_defines_careers_citation_and_conflict_handling():
    assert "cite each material claim" in SYSTEM_PROMPT
    assert "If retrieved sources conflict" in SYSTEM_PROMPT
    assert "Do not call a role active" in SYSTEM_PROMPT


def test_mock_provider_cites_numbered_context_sources():
    reply, _ = MockLLMProvider().generate_reply(
        "What internship roles are listed?",
        "Source [1]\nTitle: Careers\nURL: https://xicteksystems.com/careers\nText: roles",
    )
    assert "[1]" in reply


def test_openings_and_role_questions_are_routed_to_careers():
    assert is_careers_query("What positions are open?")
    assert is_careers_query("Are these roles remote?")
    assert is_personal_application_status_query("Can you check whether my application was received?")
    assert not is_personal_application_status_query("How long does it take to review an application?")


def test_careers_reply_can_cite_both_conflicting_sources(monkeypatch):
    store = _FakeStore([_match(text="Role is remote."), _match(text="Role is on site.")])

    class Provider:
        def generate_reply(self, message, context, history):
            assert "Source [1]" in context and "Source [2]" in context
            return "The retrieved pages conflict about the work arrangement [1] [2].", 12

    monkeypatch.setattr(service, "_load_store", lambda: store)
    monkeypatch.setattr(service, "embed_query", lambda message: np.array([1.0]))
    monkeypatch.setattr(service, "get_llm_provider", lambda: Provider())

    result = service.handle_chat(_request("Are the job roles remote?"))

    assert "pages conflict" in result.reply
    assert len(result.sources) == 2
    assert result.sources[0].url == result.sources[1].url




def test_careers_multi_turn_history_reaches_provider_and_keeps_conversation(monkeypatch):
    store = _FakeStore([_match(text="The Careers page lists internship roles.")])
    calls = []

    class Provider:
        def generate_reply(self, message, context, history):
            calls.append({"message": message, "context": context, "history": history})
            return "The page lists internship roles [1].", 7

    monkeypatch.setattr(service, "_load_store", lambda: store)
    monkeypatch.setattr(service, "embed_query", lambda message: np.array([1.0]))
    monkeypatch.setattr(service, "get_llm_provider", lambda: Provider())

    first = service.handle_chat(_request("What internship roles are listed?"))
    history = [
        {"role": "user", "content": "What internship roles are listed?"},
        {"role": "assistant", "content": first.reply},
    ]
    second_request = XictekChatRequest(
        message="What are the requirements for those roles?",
        conversation_id="careers-test",
        history=history,
    )
    second = service.handle_chat(second_request)

    assert first.conversation_id == second.conversation_id == "careers-test"
    assert len(calls) == 2
    assert calls[0]["history"] == []
    assert calls[1]["history"] == history
    assert "Source [1]" in calls[1]["context"]
    assert second.sources[0].url == "https://xicteksystems.com/careers"


def test_careers_application_status_without_evidence_uses_linked_fallback(monkeypatch):
    # Even when public retrieval finds a nearby FAQ about review time, it
    # cannot confirm the private status of this visitor's application.
    store = _FakeStore([_match(text="Applications are reviewed within 3-5 business days.")])

    class Provider:
        def generate_reply(self, *args, **kwargs):
            raise AssertionError("Unsupported application status must not reach the LLM")

    monkeypatch.setattr(service, "_load_store", lambda: store)
    monkeypatch.setattr(service, "embed_query", lambda message: np.array([1.0]))
    monkeypatch.setattr(service, "get_llm_provider", lambda: Provider())

    result = service.handle_chat(_request("Can you check whether my application was received?"))

    assert result.reply == service.CAREERS_UNVERIFIED_REPLY
    assert result.sources[0].url == service.CAREERS_SOURCE_URL
    assert result.reply.endswith("[1].")


def test_widget_creates_numbered_clickable_links_from_api_sources():
    widget = Path(__file__).resolve().parents[2] / "src" / "xictek_website_assistant" / "widget" / "xictek-widget.js"
    source = widget.read_text(encoding="utf-8")

    assert "function appendSources(sources)" in source
    assert '"[" + (i + 1) + "] "' in source
    assert "link.href = s.url" in source
    assert 'link.target = "_blank"' in source
    assert "appendSources(data.sources)" in source
