
import re



def recognize_intent(message: str) -> str:
    """Identify the user's main request."""

    text = message.lower().strip()

    # Customer balances
    if any(phrase in text for phrase in [
        "customers owe me",
        "customer balance",
        "customer balances",
        "receivable"
    ]):
        return "customer_balance"

    # Payables
    if any(phrase in text for phrase in [
        "owe my suppliers",
        "owe suppliers",
        "supplier balance",
        "payable",
        "payables"
    ]):
        return "payable"

    # Cash flow
    if any(phrase in text for phrase in [
        "cash flow",
        "cashflow"
    ]):
        return "cash_flow"

    # Financial reports
    if any(word in text for word in [
        "report", "summary", "total", "how much",
        "show my", "this week", "this month"
    ]):
        return "report"

    # Corrections
    if any(word in text for word in [
        "correct", "change", "update", "edit",
        "actually", "fix"
    ]):
        return "correction"

    # Categorization
    if any(word in text for word in [
        "categorize", "categorise", "category",
        "classify", "which category"
    ]):
        return "categorization"

    # Income
    if any(word in text for word in [
         "received", "income", "earned",
         "sales", "customer paid"
    ]):
        return "income"

    # Expenses
    if any(word in text for word in [
        "spent", "expense", "paid", "bought",
        "purchase"
    ]):
        return "expense"


    # General questions
    if any(word in text for word in [
        "what is", "how do i", "how can i",
        "help", "explain"
    ]):
        return "general_faq"

    return "unknown"

if __name__ == "__main__":
    while True:
        message = input("\nYou: ")

        if message.lower().strip() == "exit":
            break

        intent = recognize_intent(message)
        print("Detected intent:", intent)
