
import unittest
from intent_router import recognize_intent


class TestIntentRouter(unittest.TestCase):

    def test_customer_balance(self):
        self.assertEqual(
            recognize_intent("How much money do my customers owe me?"),
            "customer_balance"
        )

    def test_payable(self):
        self.assertEqual(
            recognize_intent("How much money do I owe my suppliers?"),
            "payable"
        )

    def test_cash_flow(self):
        self.assertEqual(
            recognize_intent("Show me my cash flow for this month."),
            "cash_flow"
        )

    def test_expense(self):
        self.assertEqual(
            recognize_intent("I spent 500 on groceries."),
            "expense"
        )

    def test_income(self):
        self.assertEqual(
            recognize_intent("My customer paid me 2000."),
            "income"
        )

    def test_correction(self):
        self.assertEqual(
            recognize_intent("Change the amount of my last transaction."),
            "correction"
        )

    def test_categorization(self):
        self.assertEqual(
            recognize_intent("Which category should I use for electricity bills?"),
            "categorization"
        )

    def test_unknown(self):
        self.assertEqual(
            recognize_intent("Tell me a joke."),
            "unknown"
        )


if __name__ == "__main__":
    unittest.main()
