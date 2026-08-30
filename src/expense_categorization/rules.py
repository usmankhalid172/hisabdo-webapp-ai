"""
Rule-based fallback classifier — Day 15 §6.2 calls for "rule-based fallback
+ ML/LLM model". This runs first because it's cheap, explainable, and covers
the obvious cases without needing the trained model at all.
"""
import re

# Ordered so more specific keywords are checked before generic ones.
KEYWORD_RULES: list[tuple[str, list[str]]] = [
    ("Utilities", ["electricity", "lesco", "sngpl", "gas bill", "wasa", "water bill",
                    "internet bill", "ptcl", "mobile balance", "top-up", "topup"]),
    ("Transport", ["careem", "uber", "fuel", "petrol", "parking", "bus fare",
                    "taxi", "rickshaw", "fare", "airport"]),
    ("Groceries", ["grocery", "groceries", "vegetables", "sabzi", "mandi",
                    "metro cash", "super market", "milk", "eggs"]),
    ("Dining", ["restaurant", "cafe", "coffee", "lunch", "dinner", "fast food",
                 "mcdonald", "kfc"]),
    ("Entertainment", ["movie", "cinema", "netflix", "concert", "ticket",
                         "gaming", "playstation", "spotify"]),
    ("Health", ["doctor", "hospital", "pharmacy", "clinic", "dental", "gym",
                 "medicine"]),
    ("Education", ["tuition", "school", "course", "coursera", "udemy", "books"]),
    ("Housing", ["rent", "landlord", "furniture", "maintenance", "interwood"]),
    ("Shopping", ["shoes", "clothes", "daraz", "amazon", "khaadi", "bata", "mall"]),
    ("Other", ["atm", "withdrawal", "bank fee", "donation", "charity"]),
]


def rule_based_predict(description: str, merchant: str | None) -> tuple[str, float] | None:
    """Returns (category, confidence) if a keyword rule fires, else None so
    the caller can fall back to the ML model."""
    text = f"{description} {merchant or ''}".lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    for category, keywords in KEYWORD_RULES:
        for kw in keywords:
            if kw in text:
                # Rule hits are treated as high-confidence, explainable matches.
                return category, 0.95
    return None
