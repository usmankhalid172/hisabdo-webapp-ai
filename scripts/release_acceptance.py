"""Release-candidate acceptance run for the HisabDo chatbot (POST /api/v1/chatbot).

Sends every case in data/release_acceptance_cases.json through the real FastAPI
app (mock LLM provider and mock backend, so it runs offline and is repeatable)
and checks each reply against the case's rules: which route answered, what the
reply must and must not contain, status codes, logs and cross-user state.

    python scripts/release_acceptance.py                       # print results
    python scripts/release_acceptance.py --markdown out.md     # also save a table

Exit code 1 if any CRITICAL case fails, so this can gate a release in CI.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TOKEN = "acceptance-run-token-0123456789abcdef"
os.environ["INTERNAL_SERVICE_TOKEN"] = TOKEN
os.environ["LLM_PROVIDER"] = "mock"
os.environ.setdefault("XICTEK_RATE_LIMIT", "10000/minute")

from fastapi.testclient import TestClient  # noqa: E402

from src.config import get_settings  # noqa: E402
from src.main import app  # noqa: E402

CASES_FILE = ROOT / "data" / "release_acceptance_cases.json"
PLACEHOLDER = "change-me-dev-token"


class LogCapture(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.DEBUG)
        self.records: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(f"{record.getMessage()} {record.__dict__}")


def headers_for(kind: str | None) -> dict:
    if kind == "none":
        return {}
    if kind == "wrong":
        return {"X-Internal-Token": "not-the-token"}
    return {"X-Internal-Token": TOKEN}


def post(client: TestClient, user_id: str, message: str, conversation_id: str, headers: dict):
    return client.post("/api/v1/chatbot", headers=headers,
                       json={"user_id": user_id, "message": message, "conversation_id": conversation_id, "history": []})


def check_placeholder_token_in_production() -> tuple[bool, str]:
    """With APP_ENV=production, the public placeholder token must not work."""
    saved = {k: os.environ.get(k) for k in ("INTERNAL_SERVICE_TOKEN", "APP_ENV")}
    os.environ.update({"INTERNAL_SERVICE_TOKEN": PLACEHOLDER, "APP_ENV": "production"})
    get_settings.cache_clear()
    try:
        r = post(TestClient(app, raise_server_exceptions=False), "1", "What is my balance?", "s04",
                 {"X-Internal-Token": PLACEHOLDER})
        return r.status_code != 200, f"placeholder token with APP_ENV=production -> HTTP {r.status_code}"
    finally:
        for k, v in saved.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        get_settings.cache_clear()


def run_case(client: TestClient, case: dict, capture: LogCapture) -> tuple[bool, str]:
    if case.get("check") == "placeholder_token_in_production":
        return check_placeholder_token_in_production()

    conversation_id = f"acc-{uuid.uuid4().hex[:8]}"
    for step in case.get("setup", []):
        post(client, step["user_id"], step["message"], conversation_id, headers_for(None))

    user_id = case.get("user_id", "1")
    if "raw_body" in case:
        r = client.post("/api/v1/chatbot", content=case["raw_body"],
                        headers={**headers_for(None), "Content-Type": "application/json"})
        message = ""
    else:
        message = "a" * case["message_repeat"] if "message_repeat" in case else case["message"]
        capture.records.clear()
        r = post(client, user_id, message, conversation_id, headers_for(case.get("headers")))

    notes, ok = [f"HTTP {r.status_code}"], True
    expected_status = case.get("expect_status", 200)
    if r.status_code != expected_status:
        return False, f"expected HTTP {expected_status}, got {r.status_code}"
    body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    reply = str(body.get("reply", "")) if expected_status == 200 else r.text
    # The mock model quotes the user's question back; judge only what the bot itself says.
    judged = reply.replace(message.strip(), "") if message else reply

    if "expect_source_in" in case:
        source = body.get("source")
        if source not in case["expect_source_in"]:
            ok = False
        notes.append(f"source={source}")
    for pattern in case.get("must_not_match", []):
        if re.search(pattern, judged):
            ok = False
            notes.append(f"contains /{pattern}/")
    if case.get("must_match_any") and not any(re.search(p, judged) for p in case["must_match_any"]):
        ok = False
        notes.append(f"missing any of {case['must_match_any']}")
    if case.get("expect_no_action") and (body.get("action") or (body.get("dialogue") or {}).get("status") == "completed"):
        ok = False
        notes.append("confirmed an entry it should not have")
    for secret in case.get("check_logs_exclude", []):
        if any(secret in rec for rec in capture.records):
            ok = False
            notes.append(f"logs contain {secret!r}")
    return ok, "; ".join(notes)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--markdown", help="also write the results table to this file")
    args = ap.parse_args()

    get_settings.cache_clear()
    capture = LogCapture()
    logging.getLogger().addHandler(capture)
    logging.getLogger().setLevel(logging.DEBUG)
    client = TestClient(app, raise_server_exceptions=False)

    cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))["cases"]
    rows = []
    for case in cases:
        try:
            ok, notes = run_case(client, case, capture)
        except Exception as exc:  # a crash is a failure, never a skipped case
            ok, notes = False, f"error: {type(exc).__name__}: {exc}"
        rows.append((case, ok, notes))
        print(f"{'PASS' if ok else 'FAIL'}  {case['severity']:8} {case['id']:6} {notes}")

    lines = ["| Severity | Passed |", "|---|---|"]
    for sev in ("critical", "major", "minor"):
        rs = [r for r in rows if r[0]["severity"] == sev]
        lines.append(f"| {sev} | {sum(ok for _, ok, _ in rs)}/{len(rs)} |")
    lines += ["", "| ID | Category | Severity | Question | Result | Detail | Why it matters |", "|---|---|---|---|---|---|---|"]
    for case, ok, notes in rows:
        q = case.get("message", case.get("check", "(raw request)"))
        q = f"{q[:60]}…" if len(q) > 60 else q
        lines.append(f"| {case['id']} | {case['category']} | {case['severity']} | {q.replace('|', '/')} | "
                     f"{'PASS' if ok else 'FAIL'} | {notes.replace('|', '/')} | {case['why']} |")
    table = "\n".join(lines) + "\n"
    print("\n" + "\n".join(lines[:5]))
    if args.markdown:
        Path(args.markdown).write_text(table, encoding="utf-8")
    critical_failures = [c["id"] for c, ok, _ in rows if not ok and c["severity"] == "critical"]
    print(f"\nCritical failures: {critical_failures or 'none'}")
    return 1 if critical_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
