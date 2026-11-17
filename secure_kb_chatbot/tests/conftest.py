import os
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Tests run in dev auth mode with demo data visible. These must be set before the app is
# imported. Production-mode behaviour is tested explicitly in tests/test_security.py.
os.environ.update({"AUTH_MODE": "dev", "ALLOW_DEV_AUTH": "true", "APP_ENV": "test", "ALLOW_DEMO_DATA": "true"})

from app import create_app  # noqa: E402
from chatbot import ContextBuilder, LLMResult, Repository

TODAY = date(2026, 10, 7)
SEED = Path(__file__).parent.parent / "data" / "seed.json"

# Seed users: U-001 owns B-001 (Al-Madina Traders, full data), U-101 owns
# B-002 (GreenLeaf, small data set), U-201 owns B-003 (Fresh Start, no data).
OWNER = {"X-User-Id": "U-001"}
OTHER_TENANT = {"X-User-Id": "U-101"}
EMPTY_TENANT = {"X-User-Id": "U-201"}


class FakeLLM:
    """Records what would be sent to Claude and returns scripted results."""

    def __init__(self, *results: LLMResult) -> None:
        self.results = list(results)
        self.calls: list[dict] = []

    def generate(self, system, messages):
        self.calls.append({"system": system, "messages": messages})
        if not self.results:
            return ok("Done [U-001].", ["U-001"])
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def ok(answer, citations, grounding="grounded", missing=()):
    data = {"answer": answer, "citations": list(citations), "grounding": grounding, "missing_information": list(missing)}
    return LLMResult(stop_reason="end_turn", data=data)


@pytest.fixture
def repo(tmp_path):
    r = Repository(tmp_path / "test.db")
    r.load_seed(SEED)
    return r


@pytest.fixture
def builder(repo):
    return ContextBuilder(repo)


@pytest.fixture
def llm():
    return FakeLLM()


@pytest.fixture
def client(repo, llm):
    return TestClient(create_app(repo, llm_factory=lambda: llm, today=TODAY))
