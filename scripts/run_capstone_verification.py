# Day-21 capstone integration verification script.
#
# Verifies the application/service-layer connection end to end:
#   Scenario A - in-process AssistantService fed by injected backend records
#                (simulates the HisabDo backend handing over its own data)
#   Scenario B - HTTP flow through the versioned endpoints
#                GET /v1/assistant/health and POST /v1/assistant/query
#
# Usage:
#   python scripts/run_capstone_verification.py
#   python scripts/run_capstone_verification.py \
#       --write-samples docs/samples/capstone-sample-io.json
#
# The optional --write-samples file stores every request/response pair as
# reusable sample inputs/outputs for the capstone report.

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

sys.path.insert(0, ".")

import warnings  # noqa: E402

warnings.filterwarnings(
    "ignore",
    message=r"Using .httpx. with .starlette\.testclient. is deprecated",
)
from fastapi.testclient import TestClient  # noqa: E402

from src.integration.app import app
from src.integration.service import (
    SERVICE_NAME,
    SERVICE_VERSION,
    AssistantService,
)

REFERENCE_DATE = "2026-08-20"

# Simulated HisabDo backend payload (same shape the production API would
# serve once the schema is approved).
BACKEND_RECORDS = [
    {"date": "2026-07-03", "category": "Groceries",
     "description": "Supermarket weekly shop", "amount": 60.00},
    {"date": "2026-07-10", "category": "Transport",
     "description": "Fuel fill-up", "amount": 25.50},
    {"date": "2026-07-21", "category": "Groceries",
     "description": "Local market", "amount": 39.75},
    {"date": "2026-08-05", "category": "Utilities",
     "description": "Electricity bill", "amount": 57.00},
]

SAMPLE_QUERIES = [
    ("Monthly expense (this month)", "How much did I spend this month?",
     REFERENCE_DATE),
    ("Last-month total", "What was my total spending last month?",
     REFERENCE_DATE),
    ("Highest spending category", "What is my highest spending category?",
     None),
    ("Spending summary (explicit month)",
     "Give me a spending summary for July 2026", REFERENCE_DATE),
    ("Saving tip via RAG retrieval", "Give me saving tips", None),
    ("Recurring-expenses help via RAG",
     "How do I manage recurring expenses?", None),
    ("Out-of-scope safe fallback", "Tell me a joke (unsupported check)",
     None),
]


def run_in_process_scenario() -> list:
    """Scenario A: adapter called directly with backend-injected data."""
    service = AssistantService(transactions_source=BACKEND_RECORDS)
    print("=" * 74)
    print("SCENARIO A - IN-PROCESS AssistantService (injected backend records)")
    print("=" * 74)
    health = service.health()
    print(f"\nhealth() -> {json.dumps(health)}")

    pairs = []
    for label, question, ref in SAMPLE_QUERIES:
        request = {"question": question}
        if ref:
            request["reference_date"] = ref
        out = service.ask(**request)
        print(f"\n--- {label} ---")
        print(f"request    : {json.dumps(request)}")
        print(f"status     : {out['status']}  intent={out['intent']} "
              f"period={out['period']} latency={out['latency_ms']}ms")
        print(f"validation : {out['validation']}")
        print(f"response   : {out['response']}")
        pairs.append({"scenario": "in_process_adapter", "label": label,
                      "request": request, "response": out})
    return pairs


def run_http_scenario() -> list:
    """Scenario B: same flow over HTTP via the versioned endpoints."""
    client = TestClient(app)
    print("\n" + "=" * 74)
    print("SCENARIO B - HTTP FLOW (/v1/assistant/*)")
    print("=" * 74)
    response = client.get("/v1/assistant/health")
    print(f"\nGET /v1/assistant/health -> "
          f"{response.status_code} {json.dumps(response.json())}")

    pairs = []
    for label, question, ref in SAMPLE_QUERIES:
        request = {"question": question}
        if ref:
            request["reference_date"] = ref
        r = client.post("/v1/assistant/query", json=request)
        out = r.json()
        print(f"\n--- {label} ---")
        print(f"POST /v1/assistant/query -> {r.status_code}")
        print(f"request    : {json.dumps(request)}")
        print(f"status     : {out.get('status')}  "
              f"intent={out.get('intent')} period={out.get('period')} "
              f"latency={out.get('latency_ms')}ms")
        print(f"validation : {out.get('validation')}")
        print(f"response   : {out.get('response')}")
        pairs.append({"scenario": "http_api", "label": label,
                      "request": request, "response": out})
    return pairs


def write_samples(path: str, in_process: list, http: list) -> None:
    payload = {
        "generated_by": "scripts/run_capstone_verification.py",
        "service": f"{SERVICE_NAME} {SERVICE_VERSION}",
        "generated_on": dt.date.today().isoformat(),
        "note": "Sample inputs/outputs for the capstone-integrated "
                "chatbot/RAG flow (Day 21).",
        "scenarios": {"in_process_adapter": in_process, "http_api": http},
    }
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    print(f"\nSample IO written to {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Capstone integration verification (Day 21).")
    parser.add_argument("--write-samples", metavar="PATH",
                        help="write request/response samples to PATH")
    args = parser.parse_args()

    in_process_pairs = run_in_process_scenario()
    http_pairs = run_http_scenario()
    if args.write_samples:
        write_samples(args.write_samples, in_process_pairs, http_pairs)
