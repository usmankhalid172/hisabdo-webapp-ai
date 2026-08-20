"""Test financial intent detection and use-case coverage.

This suite runs with the standard library ``unittest`` (no pytest
dependency) so it can be executed in the current environment.
"""

from __future__ import annotations

import unittest

from src.financial_assistant.intents import detect_intent, SUPPORTED_INTENTS


class IntentDetectionTests(unittest.TestCase):

    def test_monthly_expense_this_month(self):
        r = detect_intent("How much did I spend this month?")
        self.assertEqual(r.intent, "MONTHLY_EXPENSE")
        self.assertIn("period anchor", r.matched)

    def test_monthly_expense_last_month(self):
        r = detect_intent("What was my total spending last month?")
        self.assertEqual(r.intent, "MONTHLY_EXPENSE")

    def test_monthly_expense_explicit_month(self):
        r = detect_intent("What are my total expenses for July 2026?")
        if r.intent == "MONTHLY_EXPENSE":
            self.assertIsNotNone(r.period)
        else:
            self.assertEqual(r.intent, "MONTHLY_EXPENSE")

    def test_highest_category(self):
        r = detect_intent("What is my highest spending category?")
        self.assertEqual(r.intent, "HIGHEST_CATEGORY")

    def test_highest_category_with_category(self):
        r = detect_intent("Which category did I spend the most on?")
        self.assertEqual(r.intent, "HIGHEST_CATEGORY")

    def test_spending_summary(self):
        r = detect_intent("Give me a summary of my spending")
        self.assertEqual(r.intent, "SPENDING_SUMMARY")

    def test_spending_summary_month(self):
        r = detect_intent("Show me a spending breakdown for July")
        self.assertEqual(r.intent, "SPENDING_SUMMARY")

    def test_saving_tip(self):
        r = detect_intent("How can I save money?")
        self.assertEqual(r.intent, "SAVING_TIP")

    def test_saving_tip_alternate(self):
        r = detect_intent("Give me saving tips")
        self.assertEqual(r.intent, "SAVING_TIP")

    def test_greeting(self):
        r = detect_intent("hello!")
        self.assertEqual(r.intent, "GREETING")

    def test_unsupported(self):
        r = detect_intent("What is the weather in Karachi?")
        self.assertEqual(r.intent, "UNSUPPORTED")

    def test_ambiguous(self):
        r = detect_intent("I spent some money")
        self.assertEqual(r.intent, "AMBIGUOUS")

    def test_required_use_cases_are_supported(self):
        for intent in ("MONTHLY_EXPENSE", "HIGHEST_CATEGORY",
                    "SPENDING_SUMMARY", "SAVING_TIP"):
            self.assertIn(intent, SUPPORTED_INTENTS)


if __name__ == "__main__":
    unittest.main()