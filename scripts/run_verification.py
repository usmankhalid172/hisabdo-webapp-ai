# HisabDo AI Financial Assistant — feature verification script.
#
# Runs the four required use cases against the deterministic (offline) chatbot
# flow and prints terminal evidence that can be copied into the PR.

from __future__ import annotations

import datetime as dt
import sys

sys.path.insert(0, ".")

from src.financial_assistant.engine import FinancialAssistant
from src.integration.app import app
from fastapi.testclient import TestClient

QUERIES = [
    "How much did I spend this month?",
    "What was my total spending last month?",
    "What is my highest spending category?",
    "Give me a spending summary for July",
    "How can I save money?",
    "Give me saving tips",
    "Tell me a joke (unsupported check)",
]

USE_CASE_LABELS = {
    "MONTHLY_EXPENSE": "MockMonthly Expense Query",
    "HIGHEST_CATEGORY": "Highest Spending Category",
    "SPENDING_SUMMARY": "Spending-Summary Question",
    "SAVING_TIP": "Saving-Tip Request",
    "UNSUPPORTED": "Out-of-scope (blocker evidence)",
}


def run_terminal_evidence():
    assistant = FinancialAssistant(reference_date=dt.date(2026, 8, 20))
    print("=" * 74)
    print("TERMINAL EVIDENCE - AI Financial Assistant / Chatbot - RAG flow")
    print("=" * 74)
    worked = []
    unsupported = []
    for q in QUERIES:
        result = assistant.ask(q)
        label = USE_CASE_LABELS.get(result.intent, result.intent)
        print(f"\n--- {label} ---")
        print(f"Q          : {q}")
        print(f"intent     : {result.intent}  (confidence={result.confidence})")
        print(f"period     : {result.period}")
        print(f"retrieved  : {[r.chunk.title for r in result.retrieved]}")
        print(f"validation : {result.validation} {result.validation_notes}")
        print(f"answer     : {result.response}")
        if result.intent in ("MONTHLY_EXPENSE", "HIGHEST_CATEGORY",
                             "SPENDING_SUMMARY", "SAVING_TIP"):
            ok = result.validation == "pass" and bool(result.response)
            worked.append((label, ok, result.response))
        else:
            unsupported.append((label, result.intent))
    print("=" * 74)
    print("SUMMARY - supported use cases (work / status):")
    for label, ok, response in worked:
        print(f"  [{'OK' if ok else 'FAILED'}] {label}")
    print("SUMMARY - not-yet-supported use cases (blocker/evidence):")
    for label, intent in unsupported:
        print(f"  [{intent}] {label}")
    print("=" * 74)
    return worked, unsupported


def run_api_evidence():
    client = TestClient(app)
    print("API EVIDENCE - POST /chat (sample responses)")
    for q in [
        "How much did I spend this month?",
        "Which category did I spend the most on?",
        "Give me saving tips",
    ]:
        r = client.post("/chat", json={"question": q})
        payload = r.json()
        print(f"\nPOST /chat body={payload}")

    health = client.get("/health").json()
    print(f"\nGET /health -> {health}")


if __name__ == "__main__":
    run_terminal_evidence()
    run_api_evidence()