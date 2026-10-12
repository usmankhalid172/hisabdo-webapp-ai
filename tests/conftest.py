import os
import sys
from pathlib import Path

# Ensure the internal token is set before Settings is constructed.
os.environ.setdefault("INTERNAL_SERVICE_TOKEN", "test-token")
os.environ.setdefault("LLM_PROVIDER", "mock")

# Avoid rate limits during automated XICTEK tests.
os.environ.setdefault("XICTEK_RATE_LIMIT", "10000/minute")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from src.main import app
from src.security import require_authenticated_user


@pytest.fixture()
def client():
    """
    Simulate authenticated users in tests without changing
    the production authentication implementation.
    """

    def test_authenticated_user(request: Request) -> str:
        user_id = request.headers.get("X-Test-User-ID")

        if user_id and user_id.strip():
            return user_id

        return require_authenticated_user(request)

    app.dependency_overrides[require_authenticated_user] = (
        test_authenticated_user
    )

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(
            require_authenticated_user, None
        )


@pytest.fixture()
def auth_headers():
    """
    Provide the internal service token and a test user identity.
    """

    return {
        "X-Internal-Token": os.environ["INTERNAL_SERVICE_TOKEN"],
        "X-Test-User-ID": "user-1",
    }


@pytest.fixture(scope="session", autouse=True)
def ensure_categorization_model():
    """
    Automatically train the categorization model if the
    generated model file does not exist.
    """

    repo_root = Path(__file__).resolve().parents[1]
    model_path = (
        repo_root
        / "model"
        / "expense_categorization_pipeline.pkl"
    )

    if not model_path.exists():
        import subprocess

        subprocess.run(
            [
                sys.executable,
                str(
                    repo_root
                    / "src"
                    / "expense_categorization"
                    / "train_model.py"
                ),
            ],
            cwd=repo_root,
            check=True,
        )


@pytest.fixture(autouse=True)
def use_empty_xictek_index(monkeypatch, tmp_path):
    """
    Use an isolated empty vector index for tests.
    """

    from src.xictek_website_assistant import config
    from src.xictek_website_assistant import service

    monkeypatch.setattr(
        config,
        "DEFAULT_INDEX_DIR",
        tmp_path / "empty_index",
    )

    config.get_xictek_settings.cache_clear()
    service._load_store.cache_clear()

    yield

    service._load_store.cache_clear()
    config.get_xictek_settings.cache_clear()
