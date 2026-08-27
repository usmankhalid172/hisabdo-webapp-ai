import os
import sys
from pathlib import Path

# Ensure the internal token is set before Settings is constructed anywhere.
os.environ.setdefault("INTERNAL_SERVICE_TOKEN", "test-token")
os.environ.setdefault("LLM_PROVIDER", "mock")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def auth_headers():
    return {"X-Internal-Token": "test-token"}
