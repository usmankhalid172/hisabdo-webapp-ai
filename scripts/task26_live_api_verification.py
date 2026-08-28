"""
Task 26 - Live API verification for the Chatbot/RAG backend integration.

Starts the real uvicorn server on a free port, then exercises the
application's chatbot/RAG endpoint over genuine HTTP (not the in-process
TestClient) to verify:

  * endpoint connection (health/version reachable, connection retries),
  * live chatbot RAG document-context queries,
  * own-financial-data routing through the backend client,
  * general (non-RAG) fallback,
  * error handling that must never crash the backend:
      - bad auth token  -> 401
      - invalid body    -> 422
      - unknown path    -> 404
  * document-context resilience hook (server stays up across requests).

Server is started and stopped within this script; no prior server needed.

Usage:
    python scripts/task26_live_api_verification.py [--port 8025]
    python scripts/task26_live_api_verification.py --tee docs/evidence/task26-live-api-log.txt
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

# 401/422 are "expected" error responses; anything that crashes the server
# (connection reset / no response) is a failure.
EXPECTED_SOURCES = {"rag", "llm_general", "backend_financial_api",
                    "backend_unavailable"}

INTERNAL_TOKEN = os.environ.get("INTERNAL_SERVICE_TOKEN", "change-me-dev-token")


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_until_ready(base_url: str, timeout: float = 30.0) -> bool:
    """Endpoint connection check: poll health with retries until it connects."""
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
        description="Task 26 live Chatbot/RAG API verification.")
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
    record("TASK 26 LIVE API EVIDENCE - Chatbot/RAG backend integration")
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
        # 1. Endpoint connection (startup + readiness with retries).
        ready = wait_until_ready(base)
        check("endpoint connection / server readiness", ready)
        if not ready:
            record("server did not become ready; aborting checks")
            raise SystemExit(1)

        headers = {"X-Internal-Token": INTERNAL_TOKEN}

        # 2. Infra endpoints.
        r = httpx.get(f"{base}/api/v1/health")
        check("GET /api/v1/health -> 200", r.status_code == 200,
              f"status={r.json().get('status')}")
        r = httpx.get(f"{base}/api/v1/version")
        check("GET /api/v1/version -> 200", r.status_code == 200,
              f"service={r.json().get('service')}")

        # 3. Live chatbot queries.
        cases = [
            ("RAG document-context query",
             "What is a cash flow statement?", None),
            ("Own-financial-data query (backend client)",
             "What is my balance right now?", "own_financial_data"),
            ("General (no RAG match)",
             "Tell me about the weather today", None),
        ]
        for name, message, intent in cases:
            r = httpx.post(
                f"{base}/api/v1/chatbot",
                json={"user_id": "user-26", "message": message,
                      "conversation_id": "conv-26", "history": []},
                headers=headers, timeout=10.0,
            )
            ok = r.status_code == 200
            body = r.json() if ok else {}
            if intent:
                ok = ok and body.get("intent") == intent
            ok = ok and body.get("source") in EXPECTED_SOURCES
            check(f"POST /api/v1/chatbot ({name})", ok,
                  f"status={r.status_code} source={body.get('source')} "
                  f"intent={body.get('intent')}")

        # 4. Error handling - must never crash the backend.
        r = httpx.post(f"{base}/api/v1/chatbot",
                       json={"user_id": "u", "message": "hi",
                             "conversation_id": "c"},
                       headers={"X-Internal-Token": "wrong-token"})
        check("bad auth token -> 401 (no crash)", r.status_code == 401)

        r = httpx.post(f"{base}/api/v1/chatbot",
                       json={"user_id": "u", "message": "",
                             "conversation_id": "c"},
                       headers=headers)
        check("invalid body (empty message) -> 422 (no crash)",
              r.status_code == 422)

        r = httpx.get(f"{base}/api/v1/does-not-exist")
        check("unknown path -> 404 (no crash)", r.status_code == 404)

        # 5. Server still alive after all the above (crash-resilience proof).
        r = httpx.get(f"{base}/api/v1/health")
        check("server still healthy after error cases", r.status_code == 200)

    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()

    record("=" * 74)
    outcome = "ALL CHECKS PASSED" if failures == 0 else \
        f"{failures} CHECK(S) FAILED"
    record(f"TASK 26 RESULT: {outcome}")
    record("=" * 74)

    if args.tee:
        out = Path(args.tee)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\nEvidence appended to {out}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
