"""Capstone integration tests: AssistantService adapter + /v1 endpoints.

Covers the application/service-layer connection added on Day 21:
- transaction sources (default CSV, CSV path, injected backend records),
- validated inputs and structured errors,
- verified response flow over HTTP through ``/v1/assistant/*``,
- regression guard: legacy POC routes (/health, /chat) stay unaffected.
"""

from __future__ import annotations

import unittest
import warnings

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
    ServiceInputError,
)

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


class AssistantServiceTests(unittest.TestCase):
    """Adapter-level tests (in-process, no HTTP)."""

    def setUp(self):
        self.service = AssistantService(transactions_source=BACKEND_RECORDS)

    # -- data sources -------------------------------------------------- #
    def test_default_source_uses_sample_csv(self):
        payload = AssistantService().health()
        self.assertEqual(payload["data_source"], "default_csv")
        self.assertGreater(payload["transactions_loaded"], 0)

    def test_csv_path_source(self):
        service = AssistantService(
            transactions_source="data/sample_transactions.csv")
        payload = service.health()
        self.assertEqual(payload["data_source"],
                         "csv:sample_transactions.csv")
        self.assertGreater(payload["transactions_loaded"], 0)

    def test_injected_backend_records(self):
        payload = self.service.health()
        self.assertEqual(payload["data_source"], "injected_records")
        self.assertEqual(payload["transactions_loaded"], len(BACKEND_RECORDS))

    def test_malformed_injected_record_missing_field(self):
        bad = [{"date": "2026-07-01", "category": "Food"}]  # no amount
        with self.assertRaises(ServiceInputError):
            AssistantService(transactions_source=bad)

    def test_malformed_injected_record_bad_amount(self):
        bad = [{"date": "2026-07-01", "category": "Food",
                "description": "x", "amount": "abc"}]
        with self.assertRaises(ServiceInputError):
            AssistantService(transactions_source=bad)

    # -- health payload ------------------------------------------------ #
    def test_health_payload_shape(self):
        payload = self.service.health()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["service"], SERVICE_NAME)
        self.assertEqual(payload["version"], SERVICE_VERSION)
        self.assertIn("MONTHLY_EXPENSE", payload["intents_supported"])
        self.assertGreater(payload["knowledge_base_chunks"], 0)
        self.assertFalse(payload["llm_available"])

    # -- verified response flow ---------------------------------------- #
    def test_monthly_expense_with_backend_records(self):
        out = self.service.ask("How much did I spend this month?",
                               reference_date="2026-07-31")
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["intent"], "MONTHLY_EXPENSE")
        self.assertEqual(out["period"], "2026-07")
        self.assertIn("PKR 125.25", out["response"])  # 60 + 25.5 + 39.75
        self.assertIn("3 transactions", out["response"])
        self.assertEqual(out["validation"], "pass")
        self.assertGreaterEqual(out["latency_ms"], 0)

    def test_last_month_with_backend_records(self):
        out = self.service.ask("What was my total spending last month?",
                               reference_date="2026-08-20")
        self.assertEqual(out["period"], "2026-07")
        self.assertIn("PKR 125.25", out["response"])

    def test_highest_category_with_backend_records(self):
        out = self.service.ask("What is my highest spending category?")
        self.assertEqual(out["intent"], "HIGHEST_CATEGORY")
        self.assertEqual(out["facts"]["category"], "Groceries")
        self.assertEqual(out["facts"]["amount"], 99.75)  # 60 + 39.75
        self.assertIn("Groceries", out["response"])

    def test_spending_summary_for_explicit_month(self):
        out = self.service.ask("Give me a spending summary for July 2026",
                               reference_date="2026-08-20")
        self.assertEqual(out["intent"], "SPENDING_SUMMARY")
        self.assertEqual(out["period"], "2026-07")
        self.assertIn("- Groceries: PKR 99.75", out["response"])
        self.assertIn("- Transport: PKR 25.50", out["response"])

    def test_saving_tip_retrieval_flow(self):
        out = self.service.ask("Give me saving tips",
                               reference_date="2026-08-20")
        self.assertEqual(out["intent"], "SAVING_TIP")
        self.assertGreater(len(out["retrieved"]), 0)
        self.assertEqual(out["facts"]["source"], "data/saving_tips.md")

    def test_out_of_scope_safe_fallback(self):
        out = self.service.ask("Tell me a joke")
        self.assertEqual(out["intent"], "UNSUPPORTED")
        self.assertTrue(out["response"])  # non-empty grounded fallback

    # -- input validation ----------------------------------------------- #
    def test_empty_question_raises(self):
        with self.assertRaises(ServiceInputError):
            self.service.ask("")

    def test_whitespace_question_raises(self):
        with self.assertRaises(ServiceInputError):
            self.service.ask("   ")



class AssistantEndpointTests(unittest.TestCase):
    """HTTP-level tests for the versioned capstone integration routes."""

    def setUp(self):
        self.client = TestClient(app)

    def test_v1_health_endpoint(self):
        response = self.client.get("/v1/assistant/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["service"], SERVICE_NAME)
        self.assertEqual(payload["data_source"], "default_csv")
        self.assertGreater(payload["transactions_loaded"], 0)

    def test_v1_query_endpoint(self):
        response = self.client.post(
            "/v1/assistant/query",
            json={"question": "How much did I spend this month?",
                  "reference_date": "2026-08-20"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["intent"], "MONTHLY_EXPENSE")
        self.assertEqual(payload["period"], "2026-08")
        self.assertIn("PKR", payload["response"])
        self.assertEqual(payload["validation"], "pass")
        self.assertIn("latency_ms", payload)

    def test_v1_query_saving_tip_has_evidence_trace(self):
        response = self.client.post(
            "/v1/assistant/query",
            json={"question": "Give me saving tips",
                  "reference_date": "2026-08-20"},
        )
        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["intent"], "SAVING_TIP")
        self.assertGreater(len(payload["retrieved"]), 0)

    def test_v1_query_invalid_reference_date_maps_to_422(self):
        response = self.client.post(
            "/v1/assistant/query",
            json={"question": "How much did I spend this month?",
                  "reference_date": "not-a-date"},
        )
        self.assertEqual(response.status_code, 422)

    def test_v1_query_whitespace_question_maps_to_422(self):
        response = self.client.post(
            "/v1/assistant/query",
            json={"question": "   "},
        )
        self.assertEqual(response.status_code, 422)

    def test_v1_query_blank_question_fails_pydantic(self):
        response = self.client.post(
            "/v1/assistant/query",
            json={"question": ""},
        )
        self.assertEqual(response.status_code, 422)

    # -- regression guards ---------------------------------------------- #
    def test_legacy_poc_routes_still_work(self):
        health = self.client.get("/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "ok")
        chat = self.client.post(
            "/chat", json={"question": "How much did I spend last month?"})
        self.assertEqual(chat.status_code, 200)
        self.assertEqual(chat.json()["intent"], "MONTHLY_EXPENSE")


if __name__ == "__main__":
    unittest.main()

    def test_none_question_raises(self):
        with self.assertRaises(ServiceInputError):
            self.service.ask(None)

    def test_invalid_reference_date_raises(self):
        with self.assertRaises(ServiceInputError):
            self.service.ask("How much did I spend this month?",
                             reference_date="not-a-date")

    def test_non_string_reference_date_raises(self):
        with self.assertRaises(ServiceInputError):
            self.service.ask("How much did I spend this month?",
                             reference_date=20260820)

