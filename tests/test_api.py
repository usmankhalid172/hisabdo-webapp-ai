"""API integration tests using FastAPI TestClient."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

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


if __name__ == "__main__":
    unittest.main()