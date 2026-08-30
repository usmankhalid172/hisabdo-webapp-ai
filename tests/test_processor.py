"""Tests for the NLP request-processing layer (processor.py)."""

from __future__ import annotations

import datetime as dt
import unittest

from src.financial_assistant.processor import (
    ParsedRequest,
    process_question,
    resolve_period,
    resolve_relative_period,
)

REFERENCE = dt.date(2026, 8, 20)


class ProcessorTests(unittest.TestCase):

    def test_greeting_not_treated_as_financial_query(self):
        parsed = process_question("hello", REFERENCE)
        self.assertIsInstance(parsed, ParsedRequest)
        self.assertEqual(parsed.intent, "GREETING")
        self.assertIsNone(parsed.period)

    def test_explicit_month_resolution(self):
        parsed = process_question("What are my total expenses for July 2026?",
                                  REFERENCE)
        self.assertEqual(parsed.intent, "MONTHLY_EXPENSE")
        self.assertEqual(parsed.period, "2026-07")
        self.assertTrue(parsed.confidence > 0)

    def test_bare_month_name_resolved_against_reference_year(self):
        parsed = process_question("What did I spend in July?", REFERENCE)
        self.assertEqual(parsed.period, "2026-07")

    def test_relative_this_month(self):
        parsed = process_question("How much did I spend this month?",
                                  REFERENCE)
        self.assertEqual(parsed.period, "2026-08")

    def test_relative_last_month(self):
        parsed = process_question("How much did I spend last month?",
                                  REFERENCE)
        self.assertEqual(parsed.period, "2026-07")

    def test_category_scoped_request(self):
        parsed = process_question("How much did I spend on groceries in July?",
                                  REFERENCE)
        self.assertEqual(parsed.intent, "MONTHLY_EXPENSE")
        self.assertEqual(parsed.category, "Groceries")
        self.assertEqual(parsed.period, "2026-07")

    def test_entities_personal_flag(self):
        parsed = process_question("What did I spend this month?", REFERENCE)
        self.assertTrue(parsed.entities["personal"])

    def test_resolve_period_explicit_string(self):
        self.assertEqual(resolve_period("2026-07", REFERENCE), "2026-07")
        self.assertEqual(resolve_period("2026-07-15", REFERENCE), "2026-07")

    def test_resolve_period_bare_month_number(self):
        self.assertEqual(resolve_period("07", REFERENCE), "2026-07")

    def test_resolve_period_none(self):
        self.assertIsNone(resolve_period(None, REFERENCE))

    def test_resolve_relative_period(self):
        self.assertEqual(resolve_relative_period("last month", REFERENCE),
                         "2026-07")
        self.assertEqual(resolve_relative_period("this month", REFERENCE),
                         "2026-08")

    def test_unsupported_yields_unsupported_intent(self):
        parsed = process_question("What is the weather in Karachi?",
                                  REFERENCE)
        self.assertEqual(parsed.intent, "UNSUPPORTED")


if __name__ == "__main__":
    unittest.main()
