"""GeminiClient: request mapping, structured output, refusals, and error states - offline."""

import json

import pytest
from fastapi.testclient import TestClient
from google.genai import errors, types

from app import create_app
from chatbot.llm import GeminiClient, LLMUnavailable
from chatbot.prompts import RESPONSE_SCHEMA, build_system
from conftest import OWNER, TODAY

ANSWER = {"answer": "Ahmed owes PKR 85,000.00 [C-001].", "citations": ["C-001"],
          "grounding": "grounded", "missing_information": []}


def response(text=None, finish=types.FinishReason.STOP, block=None):
    parts = [types.Part(text=text)] if text is not None else []
    return types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(role="model", parts=parts), finish_reason=finish)],
        prompt_feedback=types.GenerateContentResponsePromptFeedback(block_reason=block) if block else None,
    )


class FakeModels:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class FakeGenai:
    def __init__(self, result):
        self.models = FakeModels(result)


def client_returning(result):
    return GeminiClient(model="gemini-test", client=FakeGenai(result))


def test_request_mapping_and_structured_output():
    g = client_returning(response(json.dumps(ANSWER)))
    system = build_system("<business_context>ctx</business_context>")
    messages = [
        {"role": "user", "content": "How much does Ahmed owe?"},
        {"role": "assistant", "content": "PKR 85,000.00 [C-001]."},
        {"role": "user", "content": "Any tasks for him?"},
    ]
    result = g.generate(system, messages)

    assert result.stop_reason == "end_turn" and result.data == ANSWER
    call = g.client.models.calls[0]
    assert call["model"] == "gemini-test"
    assert [c.role for c in call["contents"]] == ["user", "model", "user"]  # assistant -> model
    assert call["contents"][2].parts[0].text == "Any tasks for him?"
    cfg = call["config"]
    assert cfg.system_instruction.endswith("<business_context>ctx</business_context>")  # context injected
    assert "How to answer:" in cfg.system_instruction  # grounding rules too
    assert cfg.response_mime_type == "application/json" and cfg.response_json_schema == RESPONSE_SCHEMA


@pytest.mark.parametrize(
    "resp, category",
    [
        (response(block=types.BlockedReason.SAFETY), "safety"),
        (response(finish=types.FinishReason.PROHIBITED_CONTENT), "prohibited_content"),
    ],
)
def test_safety_blocks_become_refusals(resp, category):
    result = client_returning(resp).generate(build_system("ctx"), [{"role": "user", "content": "x"}])
    assert result.stop_reason == "refusal" and result.refusal_category == category and result.data is None


def test_truncated_output():
    result = client_returning(response('{"answer": "Ahmed ow', finish=types.FinishReason.MAX_TOKENS)).generate(
        build_system("ctx"), [{"role": "user", "content": "x"}]
    )
    assert result.stop_reason == "max_tokens" and result.data is None


@pytest.mark.parametrize(
    "error, message",
    [
        (errors.ClientError(429, {"error": {"code": 429, "message": "Quota exceeded", "status": "RESOURCE_EXHAUSTED"}}),
         "quota"),
        (errors.ClientError(400, {"error": {"code": 400, "message": "API key not valid", "status": "INVALID_ARGUMENT"}}),
         "API key"),
        (errors.ServerError(503, {"error": {"code": 503, "message": "overloaded", "status": "UNAVAILABLE"}}),
         "having problems"),
    ],
)
def test_api_errors_become_llm_unavailable(error, message):
    with pytest.raises(LLMUnavailable, match=message):
        client_returning(error).generate(build_system("ctx"), [{"role": "user", "content": "x"}])


def test_end_to_end_through_the_api(repo):
    g = client_returning(response(json.dumps(ANSWER)))
    c = TestClient(create_app(repo, llm_factory=lambda: g, today=TODAY))
    r = c.post("/api/chat", json={"message": "How much does Ahmed owe?"}, headers=OWNER)
    assert r.status_code == 200 and r.json()["grounding"] == "grounded" and r.json()["citations"] == ["C-001"]


def test_quota_exhausted_is_503_through_the_api(repo):
    g = client_returning(errors.ClientError(429, {"error": {"code": 429, "message": "Quota", "status": "x"}}))
    c = TestClient(create_app(repo, llm_factory=lambda: g, today=TODAY))
    r = c.post("/api/chat", json={"message": "hi"}, headers=OWNER)
    assert r.status_code == 503 and "quota" in r.json()["detail"]


def test_missing_gemini_key_is_503(repo, monkeypatch):
    for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENAI_USE_VERTEXAI"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("CHATBOT_PROVIDER", "gemini")
    c = TestClient(create_app(repo, today=TODAY))  # default factory -> real GeminiClient
    r = c.post("/api/chat", json={"message": "hi"}, headers=OWNER)
    assert r.status_code == 503 and "not configured" in r.json()["detail"]
    assert c.get("/api/conversations", headers=OWNER).status_code == 200  # rest of the app still works
