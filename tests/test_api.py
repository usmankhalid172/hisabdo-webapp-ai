"""API integration tests using FastAPI TestClient."""

from __future__ import annotations

import datetime as dt
import unittest
import warnings

warnings.filterwarnings(
    "ignore",
    message=r"Using .httpx. with .starlette\.testclient. is deprecated",
)
from fastapi.testclient import TestClient  # noqa: E402

from src.integration.app import app


class ApiTests(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertIn("MONTHLY_EXPENSE", payload["intents_supported"])
        self.assertGreater(payload["knowledge_base_chunks"], 0)
        self.assertGreater(payload["transactions_loaded"], 0)

    def test_chat_monthly(self):
        response = self.client.post("/chat", json={"question": "How much did I spend last month?"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["intent"], "MONTHLY_EXPENSE")
        self.assertIn("PKR", payload["response"])
        self.assertEqual(payload["validation"], "pass")

    def test_chat_saving_tip(self):
        response = self.client.post("/chat", json={"question": "Give me saving tips"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["intent"], "SAVING_TIP")
        self.assertGreater(len(payload["retrieved"]), 0)

    def test_intents_endpoint(self):
        response = self.client.post("/intents", json={"question": "What is my highest spending category?"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["intent"], "HIGHEST_CATEGORY")

    def test_invalid_ref_date(self):
        response = self.client.post(
            "/chat",
            json={"question": "How much did I spend?", "reference_date": "not-a-date"},
        )
        self.assertEqual(response.status_code, 422)

    def test_reference_date_does_not_leak_into_shared_state(self):
        # Regression for Bug C: a request with an explicit reference_date must
        # not mutate the shared assistant instance used by later requests.
        ref = self.client.post(
            "/chat",
            json={"question": "How much did I spend last month?",
                  "reference_date": "2020-01-01"},
        ).json()
        self.assertEqual(ref["period"], "2019-12")
        normal = self.client.post(
            "/chat",
            json={"question": "How much did I spend last month?"},
        ).json()
        # The default reference date is "today"; last month must NOT be the
        # leaked 2019-12 from the previous request.
        today = dt.date.today()
        year, month = today.year, today.month
        expected = f"{year-1}-12" if month == 1 else f"{year}-{month-1:02d}"
        self.assertEqual(normal["period"], expected)
        self.assertNotEqual(normal["period"], "2019-12")


if __name__ == "__main__":
    unittest.main()
