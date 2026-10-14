"""
ROUTE-xx: the intent router inside POST /api/v1/chatbot.

Checks the full HTTP path (internal token, request/response contract), the
separate routes (transaction / private backend data / FAQ RAG / general LLM),
per-(user, conversation) state, and that nothing private leaks into logs.
"""
import json
import logging

import pytest

from src.financial_assistant import service
from src.financial_assistant.dialogue.state_store import get_state_store


@pytest.fixture(autouse=True)
def fresh_state():
    get_state_store.cache_clear()
    service.get_dialogue_manager.cache_clear()
    yield
    get_state_store.cache_clear()


def send(client, headers, message, conversation_id="conv-1", user_id="user-A"):
    res = client.post("/api/v1/chatbot", headers=headers,
                      json={"user_id": user_id, "message": message, "conversation_id": conversation_id})
    assert res.status_code == 200, res.text
    return res.json()


def test_ROUTE_01_multi_turn_expense_over_http(client, auth_headers):
    r1 = send(client, auth_headers, "Ali ko 500 diye")
    assert r1["source"] == "dialogue" and r1["intent"] == "add_expense"
    assert r1["dialogue"]["status"] == "collecting" and r1["dialogue"]["missing_slots"] == ["category"]
    assert r1["dialogue"]["collected"]["amount"] == "500.00" and r1["action"] is None
    r2 = send(client, auth_headers, "sabzi aur doodh")
    assert r2["dialogue"]["status"] == "awaiting_confirmation" and "PKR 500, Groceries" in r2["reply"]
    r3 = send(client, auth_headers, "haan")
    assert r3["action"]["type"] == "create_expense" and r3["action"]["requires_client_execution"] is True
    assert r3["action"]["payload"]["category"] == "Groceries" and r3["tokens_used"] == 0


def test_ROUTE_02_state_is_per_user_and_per_conversation(client, auth_headers):
    send(client, auth_headers, "Ali ko 500 diye", conversation_id="conv-1", user_id="user-A")
    other_user = send(client, auth_headers, "haan", conversation_id="conv-1", user_id="user-B")
    assert other_user["action"] is None and other_user["dialogue"]["status"] == "none"   # B can't confirm A's entry
    other_conv = send(client, auth_headers, "haan", conversation_id="conv-2", user_id="user-A")
    assert other_conv["action"] is None
    assert send(client, auth_headers, "sabzi", conversation_id="conv-1", user_id="user-A")["dialogue"]["status"] \
        == "awaiting_confirmation"


def test_ROUTE_03_private_question_uses_backend_never_rag_or_llm(client, auth_headers, monkeypatch):
    calls = []
    monkeypatch.setattr(service, "get_retriever", lambda: (_ for _ in ()).throw(AssertionError("RAG called")))
    monkeypatch.setattr(service, "get_llm_provider", lambda: (_ for _ in ()).throw(AssertionError("LLM called")))
    real = service.get_backend_client

    def spy():
        client_ = real()
        orig = client_.get_user_financial_summary
        client_.get_user_financial_summary = lambda uid: calls.append(uid) or orig(uid)
        return client_
    monkeypatch.setattr("src.integration.backend_client.get_backend_client", spy)
    service.get_dialogue_manager.cache_clear()
    body = send(client, auth_headers, "mera balance kitna hai?")
    assert body["source"] == "backend_financial_api" and body["intent"] == "own_financial_data"
    assert "45,230.50" in body["reply"] and "demo data" in body["reply"]   # mock backend is labelled
    assert calls == ["user-A"]


def test_ROUTE_04_report_other_month_is_not_estimated(client, auth_headers):
    body = send(client, auth_headers, "pichle mahine ki report dikhao")
    assert body["source"] == "backend_financial_api" and "sirf is mahine" in body["reply"]
    assert not any(ch.isdigit() for ch in body["reply"].split("ke nahi")[1])


def test_ROUTE_05_faq_still_goes_to_rag(client, auth_headers):
    body = send(client, auth_headers, "How does automatic expense categorization work?")
    assert body["source"] == "rag" and body["intent"] == "product_faq"
    assert body["dialogue"]["route"] in ("knowledge", "general")


def test_ROUTE_06_side_question_answer_reminds_about_the_unfinished_entry(client, auth_headers):
    send(client, auth_headers, "Aaj 500 ka petrol dala")
    body = send(client, auth_headers, "What is a cash flow statement?")
    assert body["source"] in ("rag", "llm_general") and "adhoori entry abhi baqi hai" in body["reply"]
    assert send(client, auth_headers, "haan")["action"]["type"] == "create_expense"


def test_ROUTE_07_third_party_guard_still_runs_first(client, auth_headers):
    send(client, auth_headers, "Aaj 500 ka petrol dala")
    body = send(client, auth_headers, "what is my brother's balance?")
    assert body["source"] == "policy_guard" and body["intent"] == "declined_third_party"


def test_ROUTE_08_greetings_keep_the_fast_path(client, auth_headers):
    body = send(client, auth_headers, "salam")
    assert body["source"] == "greeting_fastpath"


def test_ROUTE_09_correction_over_http(client, auth_headers):
    send(client, auth_headers, "Aaj 500 ka petrol dala")
    first = send(client, auth_headers, "haan")["action"]
    send(client, auth_headers, "last wali entry 600 kar do")
    fix = send(client, auth_headers, "haan")["action"]
    assert fix["type"] == "update_transaction"
    assert fix["payload"] == {"target_action_id": first["action_id"], "changes": {"amount": "600.00"}}


def test_ROUTE_10_logs_have_no_amounts_categories_or_names(client, auth_headers, caplog):
    # The "hisabdo.ai" logger does not propagate to the root logger (logging_config.py),
    # so attach pytest's capture handler to the dialogue logger directly.
    dialogue_logger = logging.getLogger("hisabdo.ai.dialogue")
    dialogue_logger.addHandler(caplog.handler)
    dialogue_logger.setLevel(logging.INFO)
    try:
        send(client, auth_headers, "Ali ko 7777 diye")
        send(client, auth_headers, "sabzi")
        send(client, auth_headers, "haan")
    finally:
        dialogue_logger.removeHandler(caplog.handler)
    # The same record can arrive twice (directly and via propagation, depending on setup): de-duplicate.
    turns = list({id(r): r for r in caplog.records if r.getMessage() == "dialogue_turn"}.values())
    assert [r.intent for r in turns] == ["add_expense"] * 3 and turns[-1].action_type == "create_expense"
    text = json.dumps([str(r.__dict__) for r in caplog.records])
    assert "7777" not in text and "Groceries" not in text and "Ali" not in text


def test_ROUTE_11_router_crash_falls_back_to_the_old_flow(client, auth_headers, monkeypatch):
    class Broken:
        def handle(self, *a, **k):
            raise RuntimeError("bug")
    monkeypatch.setattr(service, "get_dialogue_manager", lambda: Broken())
    body = send(client, auth_headers, "What is my balance?")
    assert body["source"] == "backend_financial_api" and body["dialogue"] is None


def test_ROUTE_12_router_can_be_switched_off(client, auth_headers, monkeypatch):
    from src.config import get_settings
    monkeypatch.setattr(get_settings(), "dialogue_enabled", False)
    body = send(client, auth_headers, "Aaj 500 ka petrol dala")
    assert body["dialogue"] is None and body["source"] != "dialogue"


def test_ROUTE_13_endpoint_still_requires_the_internal_token(client):
    res = client.post("/api/v1/chatbot", json={"user_id": "u", "message": "haan", "conversation_id": "c"})
    assert res.status_code == 401
