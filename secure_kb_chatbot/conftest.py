"""Keeps this self-contained project out of the repository-wide test run.

This folder is its own app with its own `pytest.ini`, `chatbot` package and test
files (some share names with tests elsewhere in the repo). Its tests only work
when pytest runs from inside this folder:

    cd secure_kb_chatbot
    pytest

When pytest is started from the repository root, everything in this folder is
skipped, so the team's own test run is unaffected.
"""

from pathlib import Path

_HERE = Path(__file__).resolve().parent


def pytest_ignore_collect(collection_path, config):
    if Path(config.rootpath).resolve() != _HERE:
        return True
    return None
