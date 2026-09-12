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


@pytest.fixture(scope="session", autouse=True)
def ensure_categorization_model():
    """
    model/expense_categorization_pipeline.pkl is a generated binary artifact
    and is gitignored, so it never exists on a fresh clone — every clone
    needs someone to manually run train_model.py first, or every test that
    touches the real ML path fails with FileNotFoundError (has already
    happened twice: Day 28 audit, and again after a later pull).

    Session-scoped and autouse so this runs once, automatically, before any
    test in the suite — a fresh clone just works with `pytest`, no manual
    step required.
    """
    repo_root = Path(__file__).resolve().parents[1]
    model_path = repo_root / "model" / "expense_categorization_pipeline.pkl"
    if not model_path.exists():
        import subprocess

        subprocess.run(
            [
                sys.executable,
                str(repo_root / "src" / "expense_categorization" / "train_model.py"),
            ],
            cwd=repo_root,
            check=True,
        )
