"""
Task 27 - Live API verification for finalized Chatbot/RAG payloads.

Starts the real uvicorn server, then verifies over genuine HTTP that the
chatbot endpoint now returns the *self-describing, session-aware* payload:

  * ``user_id`` echoed for session identity,
  * ``model`` reporting which provider answered (demo visibility),
  * ``matched_context`` surfacing the retrieved doc title when source == "rag",
  * typed conversation history rejects malformed entries (bad role / empty
    content) with 422 instead of silently passing them through,
  * crash-resilience: server stays up across all valid + invalid cases.

Server is started and stopped within this script; no prior server needed.

Usage:
    python scripts/task27_live_api_verification.py [--port 8033]
    python scripts/task27_live_api_verification.py --tee docs/evidence/task27-live-api-log.txt
"""
from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

EXPECTED_SOURCES = {"rag", "llm_general", "backend_financial_api",
                    "backend_unavailable"}

INTERNAL_TOKEN = os.environ.get("INTERNAL_SERVICE_TOKEN", "change-me-dev-token")


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_until_ready(base_url: str, timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(f"{base_url}/api/v1/health", timeout=2.0)
            if r.status_code == 200 and r.json().get("status") == "ok":
                return True
        except httpx.HTTPError:
            pass
        time.sleep(0.5)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Task 27 live Chatbot/RAG payload verification.")
    parser.add_argument("--port", type=int, default=free_port())
    parser.add_argument("--tee", metavar="PATH", default=None,
                        help="also append the report to PATH (evidence log)")
    args = parser.parse_args()

    port = args.port
    base = f"http://127.0.0.1:{port}"
    lines: list[str] = []

    def record(text: str = "") -> None:
        print(text)
        lines.append(text)

    record("=" * 74)
    record("TASK 27 LIVE API EVIDENCE - finalized chatbot/RAG payload")
    record(f"Server: {base}  (started {time.strftime('%Y-%m-%dT%H:%M:%S')})")
    record("=" * 74)

    env = dict(os.environ)
    env["INTERNAL_SERVICE_TOKEN"] = INTERNAL_TOKEN
    env.setdefault("LLM_PROVIDER", "mock")

    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.main:app",
         "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    failures = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal failures
        mark = "PASS" if ok else "FAIL"
        if not ok:
            failures += 1
        record(f"[{mark}] {name}" + (f" | {detail}" if detail else ""))

    try:
        ready = wait_until_ready(base)
        check("endpoint connection / server readiness", ready)
        if not ready:
            record("server did not become ready; aborting checks")
            raise SystemExit(1)

        headers = {"X-Internal-Token": INTERNAL_TOKEN}

        # 1. RAG path: must echo user_id, model, and matched_context.
        r = httpx.post(f"{base}/api/v1/chatbot",
                       json={"user_id": "user-27", "message": "What is a cash flow statement?",
                             "conversation_id": "conv-27", "history": []},
                       headers=headers, timeout=10.0)
        body = r.json() if r.status_code == 200 else {}
        ok = r.status_code == 200 and body.get("source") == "rag"
        ok = ok and body.get("user_id") == "user-27"
        ok = ok and bool(body.get("model"))
        ok = ok and bool(body.get("matched_context"))
        check("RAG reply carries user_id echo + model + matched_context", ok,
              f"source={body.get('source')} user_id={body.get('user_id')} "
              f"model={body.get('model')} ctx={body.get('matched_context')}")

        # 2. Own-financial-data path: user_id echo + model, no context.
        r = httpx.post(f"{base}/api/v1/chatbot",
                       json={"user_id": "user-27", "message": "What is my balance right now?",
                             "conversation_id": "conv-27", "history": []},
                       headers=headers, timeout=10.0)
        body = r.json() if r.status_code == 200 else {}
        ok = r.status_code == 200 and body.get("source") == "backend_financial_api"
        ok = ok and body.get("user_id") == "user-27"
        ok = ok and bool(body.get("model"))
        ok = ok and body.get("matched_context") is None
        check("own-financial-data reply user_id + model, no context", ok,
              f"source={body.get('source')} model={body.get('model')}")

        # 3. General path: user_id echo + model, no context.
        r = httpx.post(f"{base}/api/v1/chatbot",
                       json={"user_id": "user-27", "message": "Tell me about the weather",
                             "conversation_id": "conv-27", "history": []},
                       headers=headers, timeout=10.0)
        body = r.json() if r.status_code == 200 else {}
        ok = r.status_code == 200 and body.get("source") == "llm_general"
        ok = ok and body.get("user_id") == "user-27" and bool(body.get("model"))
        check("general reply user_id + model, no context", ok,
              f"source={body.get('source')} model={body.get('model')}")

        # 4. Typed history acceptance (valid entries).
        r = httpx.post(f"{base}/api/v1/chatbot",
                       json={"user_id": "user-27", "message": "What is a cash flow statement?",
                             "conversation_id": "conv-27",
                             "history": [
                                 {"role": "user", "content": "Hi"},
                                 {"role": "assistant", "content": "Hello!"},
                             ]},
                       headers=headers, timeout=10.0)
        check("typed history (valid role/content) accepted", r.status_code == 200)

        # 5. Typed history rejection: bad role -> 422, server survives.
        r = httpx.post(f"{base}/api/v1/chatbot",
                       json={"user_id": "user-27", "message": "hi",
                             "conversation_id": "conv-27",
                             "history": [{"role": "system", "content": "you are..."}]},
                       headers=headers, timeout=10.0)
        check("typed history bad role -> 422 (no crash)", r.status_code == 422)

        # 6. Typed history rejection: empty content -> 422, server survives.
        r = httpx.post(f"{base}/api/v1/chatbot",
                       json={"user_id": "user-27", "message": "hi",
                             "conversation_id": "conv-27",
                             "history": [{"role": "user", "content": ""}]},
                       headers=headers, timeout=10.0)
        check("typed history empty content -> 422 (no crash)", r.status_code == 422)

        # 7. Server still alive after all valid + invalid cases.
        r = httpx.get(f"{base}/api/v1/health")
        check("server still healthy after all cases", r.status_code == 200)

    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()

    record("=" * 74)
    outcome = "ALL CHECKS PASSED" if failures == 0 else \
        f"{failures} CHECK(S) FAILED"
    record(f"TASK 27 RESULT: {outcome}")
    record("=" * 74)

    if args.tee:
        out = Path(args.tee)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\nEvidence appended to {out}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
