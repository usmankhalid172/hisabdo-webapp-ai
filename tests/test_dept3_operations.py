"""Department 3 operations: safe telemetry, metrics, fallbacks, index updates, router fixes
(docs/dept3-monitoring-runbook.md, docs/dept3-quality-scorecard.md)."""

import json
from datetime import date

import pytest

from src.config import get_settings
from src.financial_assistant import service, telemetry
from src.financial_assistant.dialogue.recognizer import RuleBasedIntentRecognizer
from src.financial_assistant.grounding import retrieval as kbr
from src.financial_assistant.grounding.retrieval import KB_PATH, load_kb, validate_kb


@pytest.fixture()
def events(monkeypatch):
    seen = []

    class Capture:
        def info(self, msg, extra=None):
            seen.append(extra["turn"])

    monkeypatch.setattr(telemetry, "log", Capture())
    telemetry.METRICS.reset()
    return seen


@pytest.fixture()
def grounded(monkeypatch):
    monkeypatch.setenv("GROUNDED_ANSWERS_ENABLED", "true")
    monkeypatch.setenv("KB_RETRIEVER_MODE", "lexical")
    get_settings.cache_clear()
    service.get_grounded_answerer.cache_clear()
    yield
    get_settings.cache_clear()
    service.get_grounded_answerer.cache_clear()


def send(client, headers, message, user="user-ops-1"):
    r = client.post("/api/v1/chatbot", headers=headers, json={"user_id": user, "message": message, "conversation_id": "ops"})
    assert r.status_code == 200, r.text
    return r.json()


# Safe logging --------------------------------------------------------------------------------------------------

def test_turn_events_carry_only_allowlisted_fields_and_no_user_content(client, auth_headers, events, grounded):
    send(client, auth_headers, "Is HisabDo free to use?")
    send(client, auth_headers, "What is my balance?")
    send(client, auth_headers, "Ali ko 500 diye, mera number 0300-1234567")
    assert len(events) == 3
    for e in events:
        assert set(e) <= set(telemetry.SAFE_FIELDS)
        blob = json.dumps(e)
        for forbidden in ("free to use", "balance?", "Ali ko", "0300", "user-ops-1", "500",
                          get_settings().internal_service_token):
            assert forbidden not in blob, forbidden
        assert len(e["user_ref"]) == 12 and e["latency_ms"] >= 0
    k = events[0]
    assert k["route"] == "knowledge" and k["retrieved_ids"] and k["cited_ids"] and k["retrieval_mode"] == "lexical"
    assert events[1]["route"] == "account_data" and events[2]["route"] == "transaction"


def test_safe_event_drops_unknown_fields_and_redacts_identifiers():
    e = telemetry.safe_event(route="knowledge", message="my CNIC is 35202-1234567-1", intent="Rs. 5000 paid",
                             error_category="none")
    assert "message" not in e and e["intent"] == "[redacted]" and e["route"] == "knowledge"


def test_metrics_endpoint_reports_counters_latency_and_kb_status(client, auth_headers, events, grounded):
    send(client, auth_headers, "Is HisabDo free to use?")
    send(client, auth_headers, "Does HisabDo have a desktop app for Mac?")
    m = client.get("/api/v1/metrics", headers=auth_headers).json()
    assert m["counters"]["turns"] == 2 and m["counters"]["fallback:no_source"] == 1
    assert m["latency"]["knowledge"]["n"] == 2 and m["kb"]["loaded"] and m["kb"]["chunks"] > 300
    assert client.get("/api/v1/metrics").status_code == 401


# Fallbacks -----------------------------------------------------------------------------------------------------

class Broken:
    def generate_reply(self, message, context=None, history=None):
        raise TimeoutError("provider timed out")


def test_llm_failure_on_general_route_gives_a_safe_reply(client, auth_headers, events, monkeypatch):
    monkeypatch.setattr(service, "get_llm_provider", lambda: Broken())
    r = send(client, auth_headers, "How do I keep my business records organised?")
    assert r["source"] in ("llm_unavailable", "rag")
    if r["source"] == "llm_unavailable":
        assert "try again" in r["reply"] and events[-1]["error_category"] == "llm_timeout"


def test_llm_failure_on_own_figures_returns_the_exact_backend_figures(client, auth_headers, events, monkeypatch):
    monkeypatch.setattr(service, "get_llm_provider", lambda: Broken())
    monkeypatch.setattr(service, "_run_dialogue", lambda req: (None, None))
    r = send(client, auth_headers, "What is my balance?")
    assert r["source"] == "backend_financial_api" and r["reply"].startswith("Balance:")
    assert events[-1]["fallback"] == "llm_error"


def test_backend_failure_never_estimates_figures(client, auth_headers, events, monkeypatch):
    class Down:
        def get_user_financial_summary(self, user_id):
            raise ConnectionError("backend down")

    monkeypatch.setattr(service, "get_backend_client", lambda: Down())
    monkeypatch.setattr(service, "_run_dialogue", lambda req: (None, None))
    r = send(client, auth_headers, "What is my balance?")
    assert r["source"] == "backend_unavailable" and "won't estimate" in r["reply"]
    assert not any(ch.isdigit() for ch in r["reply"]) and events[-1]["error_category"] == "backend_error"


def test_grounded_answer_survives_a_model_error_with_its_sources(client, auth_headers, events, grounded, monkeypatch):
    monkeypatch.setattr(service, "get_llm_provider", lambda: Broken())
    r = send(client, auth_headers, "Is HisabDo free to use?")
    assert r["answer_status"] == "answered" and r["citations"] and events[-1]["error_category"] == "llm_error"


def test_index_build_failure_serves_the_kb_unavailable_fallback_and_retries_later(client, auth_headers, events,
                                                                                   grounded, monkeypatch):
    def boom(*a, **k):
        raise OSError("kb file missing")

    monkeypatch.setattr(service, "KbRetriever", boom)
    service.get_grounded_answerer.cache_clear()
    r = send(client, auth_headers, "Is HisabDo free to use?")
    assert r["source"] == "kb_unavailable" and "won't guess" in r["reply"]
    assert events[-1]["error_category"] == "kb_unavailable"
    monkeypatch.undo()
    assert service.get_grounded_answerer() is None  # still inside the retry interval: no rebuild storm


def test_empty_retrieval_is_a_counted_fallback(client, auth_headers, events, grounded):
    r = send(client, auth_headers, "Does HisabDo have a desktop app for Mac?")
    assert r["answer_status"] == "no_source" and events[-1]["fallback"] == "no_source"


def test_unexpected_error_becomes_a_safe_reply_not_a_stack_trace(client, auth_headers, events, monkeypatch):
    monkeypatch.setattr(service, "_handle_chat", lambda req: 1 / 0)
    r = send(client, auth_headers, "Is HisabDo free to use?")
    assert r["source"] == "service_fallback" and "Traceback" not in r["reply"]
    assert events[-1]["error_category"] == "internal_error"


def test_dense_model_failure_degrades_to_lexical(monkeypatch):
    import builtins
    real = builtins.__import__

    def no_fastembed(name, *a, **k):
        if name == "fastembed":
            raise RuntimeError("model download failed")
        return real(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", no_fastembed)
    r = kbr.KbRetriever(mode="auto")
    assert r.mode == "lexical" and r.degraded == "dense_unavailable:RuntimeError"


# Index updates -------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("change,reason", [
    (lambda cs: cs[:100], "shrunk"), (lambda cs: cs + [cs[0]], "duplicate_ids"),
    (lambda cs: [{**cs[0], "body": cs[0]["body"] + " Call 0300-1234567."}] + cs[1:], "personal_identifier"),
    (lambda cs: [{k: v for k, v in cs[0].items() if k != "source_url"}] + cs[1:], "missing_fields")])
def test_invalid_index_updates_are_rejected_and_the_current_index_keeps_serving(tmp_path, grounded, change, reason):
    current = service.get_grounded_answerer()
    bad = tmp_path / "kb.jsonl"
    bad.write_text("\n".join(json.dumps(c) for c in change(load_kb())), encoding="utf-8")
    res = service.reload_kb(bad)
    assert not res["updated"] and any(r.startswith(reason) for r in res["reasons"])
    assert service.get_grounded_answerer() is current


def test_unreadable_update_is_rejected(tmp_path):
    bad = tmp_path / "kb.jsonl"
    bad.write_text("{not json", encoding="utf-8")
    ok, reasons, _ = validate_kb(bad)
    assert not ok and reasons[0].startswith("unreadable")


def test_valid_update_is_swapped_in(grounded):
    assert service.reload_kb(KB_PATH)["updated"] is True and service.kb_status()["loaded"]


# Router fixes (docs/dept3-quality-scorecard.md) ------------------------------------------------------------------

@pytest.mark.parametrize("message,expected", [
    ("Is my khata safe if I change my phone?", "faq"),
    ("Udhar aur payment mein kya farq hai?", "faq"),
    ("ادھار اور ادائیگی میں کیا فرق ہے؟", "faq"),
    ("What is the capital of France?", "general"),
    ("How do I install Python on Windows?", "general"),
    ("What is my customer's phone number?", "account_query"),
    ("Should I register my shop for sales tax?", "faq"),
    ("How long does HisabDo keep my data after I delete my account?", "faq"),
    ("Who won the 1992 cricket world cup?", "general"),
    # unchanged behaviour
    ("What are my total sales?", "report"), ("Ali ko 500 diye", "add_expense"),
    ("What is HisabDo?", "faq")])
# Still open (missed before and after this change): "galti ho gayi, 450 nahi 540 tha" -> general, not a correction.
def test_router_fixes(message, expected):
    got = RuleBasedIntentRecognizer().recognize(message, date(2026, 11, 3)).intent.value
    assert got == expected or (expected == "general" and got == "general"), (message, got)
