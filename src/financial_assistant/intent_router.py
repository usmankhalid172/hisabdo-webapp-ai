import re
from decimal import Decimal, InvalidOperation


INTENTS = {
    "expense": (
        r"\b(add|record|log|save|enter)\b.*\b(expense|spent|spending|purchase)\b",
        r"\b(expense|spent|spending)\b.*\b(add|record|log)\b",
    ),
    "income": (
        r"\b(add|record|log|save|enter)\b.*\b(income|revenue|earning|sale)\b",
        r"\b(income|revenue|earning|sale)\b.*\b(add|record|log)\b",
    ),
    "correction": (
        r"\b(correct|edit|update|change|fix|modify)\b.*\b(expense|income|transaction|amount|category)\b",
        r"\b(incorrect|wrong|mistake|correction)\b",
    ),
    "report": (
        r"\b(report|summary|breakdown|statement|total)\b",
        r"\b(show|view|generate)\b.*\b(expenses|income|sales|profit)\b",
    ),
    "categorization": (
        r"\b(categorize|categorise|category|categorization|categorisation)\b",
    ),
}


def classify_intent(message: str) -> str:
    """Classify a message without calling an LLM."""
    text = message.lower().strip()

    for intent, patterns in INTENTS.items():
        if any(re.search(pattern, text) for pattern in patterns):
            return intent

    if re.search(
        r"\b(my balance|my expenses|my revenue|how much did i spend|"
        r"my outstanding|my profit|my sales)\b",
        text,
    ):
        return "private_account_query"

    return "general_faq"


def extract_slots(message: str) -> dict:
    """Extract basic transaction fields from a user message."""
    text = message.strip()
    slots = {}

    amount_match = re.search(
        r"(?<!\w)(?:rs\.?|pkr|₨)\s*([\d,]+(?:\.\d{1,2})?)"
        r"|(?<!\w)([\d,]+(?:\.\d{1,2})?)\s*(?:pkr|rupees?|rs\.?)\b",
        text,
        re.IGNORECASE,
    )

    if amount_match:
        raw_amount = next(
            (group for group in amount_match.groups() if group is not None),
            None,
        )
        if raw_amount:
            try:
                amount = Decimal(raw_amount.replace(",", ""))
                if amount > 0:
                    slots["amount"] = str(amount)
            except InvalidOperation:
                pass

    description_match = re.search(
        r"\b(?:for|on)\s+(.+)$",
        message,
        re.IGNORECASE,
    )
    if description_match:
        slots["description"] = description_match.group(1).strip(" .,")

    category_match = re.search(
        r"\b(food|groceries|transport|fuel|rent|utilities|"
        r"salary|supplies|marketing|health|education)\b",
        text,
        re.IGNORECASE,
    )
    if category_match:
        slots["category"] = category_match.group(1).lower()

    return slots


def get_missing_fields(intent: str, slots: dict) -> list[str]:
    """Return required fields for a new expense or income."""
    if intent not in {"expense", "income"}:
        return []

    required = ["amount", "description"]
    return [field for field in required if not slots.get(field)]


def build_follow_up(intent: str, missing_fields: list[str]) -> str:
    """Ask for missing transaction details."""
    questions = {
        "amount": "What was the amount?",
        "description": "Please describe the transaction.",
    }

    if not missing_fields:
        return ""

    if len(missing_fields) == 1:
        return questions[missing_fields[0]]

    return "Please provide the transaction amount and description."
