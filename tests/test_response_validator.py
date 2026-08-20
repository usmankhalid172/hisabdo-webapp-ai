"""Response validator tests: grounding + scope guards."""

from __future__ import annotations

import unittest

from src.financial_assistant import response_validator as v


class ValidationTests(unittest.TestCase):

    FACTS_OK = {
        "period": "2026-07",
        "total": 100.0,
        "count": 3,
        "categories": {"Groceries": 60.0, "Dining Out": 40.0},
    }

    def test_grounded_response_passes(self):
        text = "Your total spending in July 2026 was PKR 100.00."
        result = v.validate_response("MONTHLY_EXPENSE", text, self.FACTS_OK)
        self.assertTrue(result.ok)

    def test_empty_response_fails(self):
        result = v.validate_response("SAVING_TIP", "   ")
        self.assertFalse(result.ok)
        self.assertIn("empty response", result.issues)

    def test_ungrounded_amount_fails(self):
        text = "Your total spending in July was PKR 4,999.00."
        result = v.validate_response("MONTHLY_EXPENSE", text, self.FACTS_OK)
        self.assertFalse(result.ok)
        self.assertTrue(any("ungrounded" in issue for issue in result.issues))

    def test_overlong_response_fails(self):
        long_text = "word " * 300
        result = v.validate_response("SAVING_TIP", long_text)
        self.assertFalse(result.ok)


if __name__ == "__main__":
    unittest.main()