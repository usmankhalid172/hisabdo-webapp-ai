"""SQA: Empty states and error states."""

import sqlite3

import anthropic
import pytest

from chatbot import LLMResult
from chatbot.llm import LLMUnavailable
from conftest import EMPTY_TENANT, OWNER, ok

KINDS = ["customers", "tasks", "notes", "receivables", "payables"]

# --- empty states -------------------------------------------------------------------


@pytest.mark.parametrize("kind", KINDS)
def test_empty_business_lists_are_empty_arrays(client, kind):
    r = client.get(f"/api/{kind}", headers=EMPTY_TENANT)
    assert r.status_code == 200 and r.json() == []


def test_empty_business_context_is_explicit(builder):
    from conftest import TODAY

    b = builder.build("U-201", "How much does Ahmed owe?", TODAY)
    for tag in ("<customers/>", "<receivables/>", "<payables/>", "<tasks/>", "<notes/>"):
        assert tag in b.text
    assert '<customers total="0"' in b.text
    assert 'open_count="0" outstanding_total="0.00"' in b.text
    assert b.included == {"customers": [], "receivables": [], "payables": [], "tasks": [], "notes": []}


def test_empty_business_chat_still_answers(client, llm):
    llm.results = [ok("You don't have any customers recorded yet, so there's no Ahmed [B-003].", ["B-003"],
                      grounding="insufficient_data", missing=["customer named Ahmed"])]
    r = client.post("/api/chat", json={"message": "How much does Ahmed owe?"}, headers=EMPTY_TENANT)
    assert r.status_code == 200
    assert r.json()["grounding"] == "insufficient_data"
    assert r.json()["context"]["totals"]["customers"] == 0


def test_question_with_no_matching_records(builder):
    from conftest import TODAY

    b = builder.build("U-001", "How much does Zubair owe?", TODAY)
    assert b.focus_customer_ids == []
    assert "Zubair" not in b.text  # nothing invented; the model sees no such customer
    assert 'exist="5"' in b.text  # ...and knows how many customers exist in total


# --- error states ---------------------------------------------------------------------


def test_missing_user_header_is_401(client):
    assert client.get("/api/customers").status_code == 401
    assert client.post("/api/chat", json={"message": "hi"}).status_code == 401


def test_unknown_user_is_401(client):
    assert client.get("/api/customers", headers={"X-User-Id": "U-999"}).status_code == 401


@pytest.mark.parametrize("kind", KINDS)
def test_unknown_record_is_404(client, kind):
    for method in ("get", "patch", "delete"):
        kwargs = {"json": {}} if method == "patch" else {}
        r = getattr(client, method)(f"/api/{kind}/X-404", headers=OWNER, **kwargs)
        assert r.status_code == 404 and r.json() == {"detail": "Record not found"}


def test_delete_customer_with_invoices_is_409(client):
    r = client.delete("/api/customers/C-001", headers=OWNER)
    assert r.status_code == 409
    assert client.get("/api/customers/C-001", headers=OWNER).status_code == 200  # nothing deleted


def test_unknown_conversation_is_404(client):
    r = client.post("/api/chat", json={"message": "hi", "conversation_id": "nope"}, headers=OWNER)
    assert r.status_code == 404


def test_ai_unavailable_is_503(client, llm):
    llm.results = [LLMUnavailable("Could not reach the assistant service.")]
    r = client.post("/api/chat", json={"message": "hi"}, headers=OWNER)
    assert r.status_code == 503 and "reach" in r.json()["detail"]


def test_ai_not_configured_is_503_but_crud_still_works(repo):
    from fastapi.testclient import TestClient

    from app import create_app

    def no_key():
        raise anthropic.AnthropicError("no API key")

    c = TestClient(create_app(repo, llm_factory=no_key))
    assert c.post("/api/chat", json={"message": "hi"}, headers=OWNER).status_code == 503
    assert c.get("/api/customers", headers=OWNER).status_code == 200


def test_database_error_is_503_without_leaking_details(client, repo, monkeypatch):
    def broken(*a, **k):
        raise sqlite3.OperationalError("disk I/O error at /secret/path")

    monkeypatch.setattr(repo, "list", broken)
    r = client.get("/api/customers", headers=OWNER)
    assert r.status_code == 503 and "secret" not in r.text


def test_model_refusal_is_reported_not_crashed(client, llm):
    llm.results = [LLMResult(stop_reason="refusal", data=None, refusal_category="cyber")]
    r = client.post("/api/chat", json={"message": "hi"}, headers=OWNER).json()
    assert r["grounding"] == "refused" and "cyber" in r["warnings"][0]


def test_truncated_model_output_is_reported(client, llm):
    llm.results = [LLMResult(stop_reason="max_tokens", data=None)]
    r = client.post("/api/chat", json={"message": "hi"}, headers=OWNER).json()
    assert r["grounding"] == "error"


def test_missing_api_key_is_503_not_500(repo, monkeypatch):
    """Real ClaudeClient with no credentials: the SDK fails at request time."""
    from fastapi.testclient import TestClient

    from app import create_app
    from chatbot.llm import ClaudeClient

    for var in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_PROFILE"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("ANTHROPIC_CONFIG_DIR", str(repo.path) + ".noconfig")
    c = TestClient(create_app(repo, llm_factory=lambda: ClaudeClient(client=anthropic.Anthropic(api_key=None, max_retries=0))))
    r = c.post("/api/chat", json={"message": "How much does Ahmed owe?"}, headers=OWNER)
    assert r.status_code == 503 and "not configured" in r.json()["detail"]
