
import logging

from types import SimpleNamespace

from src.financial_assistant.monitoring import (
    MonitoringCounters,
    safe_log_event,
    start_timer,
    elapsed_ms,
)

from src.financial_assistant import faq_rag


def test_safe_log_event_does_not_log_unapproved_values(caplog):
    with caplog.at_level(
        logging.INFO,
        logger="financial_assistant.monitoring",
    ):
        safe_log_event(
            "private-user-message",
            outcome="success",
            component="private-financial-data",
            provider="secret-api-key",
            model="private-model-name",
            retrieved_source_ids=[
                "faq-001",
                "user-account-12345",
                "PKR-50000",
            ],
            error_category="private-exception",
        )

    output = caplog.text

    assert "private-user-message" not in output
    assert "secret-api-key" not in output
    assert "private-model-name" not in output
    assert "user-account-12345" not in output
    assert "PKR-50000" not in output
    assert "faq-001" in output


def test_safe_log_event_accepts_valid_provider_metadata(caplog):
    with caplog.at_level(
        logging.INFO,
        logger="financial_assistant.monitoring",
    ):
        safe_log_event(
            "provider_call",
            outcome="success",
            component="provider",
            provider="openai",
            model="gpt-4o-mini",
            input_tokens=100,
            output_tokens=50,
        )

    assert "openai" in caplog.text
    assert "gpt-4o-mini" in caplog.text
    assert "100" in caplog.text
    assert "50" in caplog.text


def test_monitoring_counters_increment_safely():
    counters = MonitoringCounters()

    counters.increment("requests")
    counters.increment("success", 2)
    counters.increment("unknown_private_field")
    counters.increment("errors", -1)

    result = counters.snapshot()

    assert result["requests"] == 1
    assert result["success"] == 2
    assert "unknown_private_field" not in result
    assert result["errors"] == 0


def test_timer_returns_non_negative_latency():
    started = start_timer()

    assert elapsed_ms(started) >= 0


def test_failed_index_rebuild_retains_previous_index(monkeypatch):
    retriever = faq_rag.FaqRetriever.__new__(
        faq_rag.FaqRetriever
    )

    old_documents = [object()]
    old_vector_store = object()

    retriever.documents = old_documents
    retriever.vector_store = old_vector_store
    retriever.docs_path = faq_rag.DOCS_PATH
    retriever.relevance_threshold = 0.40
    retriever.model_name = faq_rag.DEFAULT_MODEL_NAME

    def fail_replacement(*args, **kwargs):
        raise RuntimeError("private failure details")

    monkeypatch.setattr(
        faq_rag,
        "FaqRetriever",
        fail_replacement,
    )

    result = retriever.rebuild_index()

    assert result is False
    assert retriever.documents is old_documents
    assert retriever.vector_store is old_vector_store


def test_successful_index_rebuild_swaps_index(monkeypatch):
    retriever = faq_rag.FaqRetriever.__new__(
        faq_rag.FaqRetriever
    )

    old_documents = [object()]
    old_vector_store = object()

    retriever.documents = old_documents
    retriever.vector_store = old_vector_store
    retriever.docs_path = faq_rag.DOCS_PATH
    retriever.relevance_threshold = 0.40
    retriever.model_name = faq_rag.DEFAULT_MODEL_NAME

    new_documents = [object()]
    new_vector_store = object()

    def build_replacement(*args, **kwargs):
        return SimpleNamespace(
            documents=new_documents,
            vector_store=new_vector_store,
        )

    monkeypatch.setattr(
        faq_rag,
        "FaqRetriever",
        build_replacement,
    )

    result = retriever.rebuild_index()

    assert result is True
    assert retriever.documents is new_documents
    assert retriever.vector_store is new_vector_store


def test_empty_retrieval_returns_safe_empty_list():
    retriever = faq_rag.FaqRetriever.__new__(
        faq_rag.FaqRetriever
    )

    retriever.vector_store = None
    retriever._uses_default_knowledge_base = False

    result = retriever.retrieve("What is my balance?")

    assert result == []


def test_invalid_retrieval_input_returns_empty_list():
    retriever = faq_rag.FaqRetriever.__new__(
        faq_rag.FaqRetriever
    )

    retriever.vector_store = None
    retriever._uses_default_knowledge_base = False

    assert retriever.retrieve("") == []
    assert retriever.retrieve("   ") == []
    assert retriever.retrieve("Valid query", top_k=0) == []
def test_provider_failure_is_recorded_and_exception_is_raised(monkeypatch):
    import pytest
    from src.financial_assistant import llm_providers

    recorded = []

    def fake_record_provider_failure(provider, model, started_at):
        recorded.append((provider, model, started_at))

    monkeypatch.setattr(
        llm_providers,
        "record_provider_failure",
        fake_record_provider_failure,
    )

    @llm_providers._monitor_provider_errors("openai", "test-model")
    def failing_call(self):
        raise RuntimeError("test failure")

    class DummyProvider:
        generate_reply = failing_call

    with pytest.raises(RuntimeError, match="test failure"):
        DummyProvider().generate_reply()

    assert len(recorded) == 1
    assert recorded[0][0] == "openai"
    assert recorded[0][1] == "test-model"
    assert isinstance(recorded[0][2], float)