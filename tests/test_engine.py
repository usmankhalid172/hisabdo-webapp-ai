"""End-to-end engine tests for the four required use cases.

Covers the chatbot flow: intent -> facts -> grounded response -> validation.
"""

from __future__ import annotations

import datetime as dt
import unittest

from src.financial_assistant.engine import FinancialAssistant

REFERENCE = dt.date(2026, 8, 20)


class AssistantUseCaseTests(unittest.TestCase):

    def setUp(self):
        self.assistant = FinancialAssistant(reference_date=REFERENCE)

    def test_monthly_expense_this_month(self):
        result = self.assistant.ask("How much did I spend this month?")
        self.assertEqual(result.intent, "MONTHLY_EXPENSE")
        self.assertEqual(result.period, "2026-08")
        self.assertIn("PKR", result.response)
        self.assertEqual(result.validation, "pass")
        self.assertGreater(result.facts["total"], 0)

    def test_monthly_expense_last_month(self):
        result = self.assistant.ask("What was my total spending last month?")
        self.assertEqual(result.intent, "MONTHLY_EXPENSE")
        self.assertEqual(result.period, "2026-07")
        self.assertIn("July 2026", result.response)
        self.assertEqual(result.validation, "pass")

    def test_highest_spending_category(self):
        result = self.assistant.ask("Which category did I spend the most on?")
        self.assertEqual(result.intent, "HIGHEST_CATEGORY")
        self.assertIn("Groceries", result.response)
        self.assertEqual(result.validation, "pass")

    def test_spending_summary_july(self):
        result = self.assistant.ask("Give me a spending summary for July")
        self.assertEqual(result.intent, "SPENDING_SUMMARY")
        self.assertEqual(result.period, "2026-07")
        for cat in result.facts.get("categories", {}):
            self.assertIn(cat, result.response)
        self.assertEqual(result.validation, "pass")

    def test_saving_tip_retrieval(self):
        result = self.assistant.ask("How can I save money?")
        self.assertEqual(result.intent, "SAVING_TIP")
        self.assertGreater(len(result.retrieved), 0)
        self.assertNotIn("retrieved chunk", result.response)  # grounded text
        self.assertEqual(result.validation, "pass")

    def test_unsupported_question(self):
        result = self.assistant.ask("Tell me a joke")
        self.assertEqual(result.intent, "UNSUPPORTED")
        self.assertIn("financial assistant", result.response)

    def test_ambiguous_question(self):
        result = self.assistant.ask("How much did I spend?")
        # No period is resolvable, so the assistant should ask for clarification.
        self.assertIsNone(result.period)
        self.assertIn("which time period", result.response.lower())

    def test_greeting(self):
        result = self.assistant.ask("Hello!")
        self.assertEqual(result.intent, "GREETING")

    def test_no_hallucination_missing_period_data(self):
        # A month with no data must not produce an invented figure.
        result = self.assistant.ask("How much did I spend in January 2025?")
        self.assertEqual(result.intent, "MONTHLY_EXPENSE")
        self.assertNotIn("PKR", result.response)

    def test_highest_category_empty_month(self):
        # Regression for Bug B: a month with no transactions must produce a
        # clean 'no data' message, not "? at PKR 0.00".
        result = self.assistant.ask("What is my highest spending category "
                                    "in January 2025?")
        self.assertEqual(result.intent, "HIGHEST_CATEGORY")
        self.assertNotIn("?", result.response)
        self.assertIn("could not find any", result.response.lower())


if __name__ == "__main__":
    unittest.main()
