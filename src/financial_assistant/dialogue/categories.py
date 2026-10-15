"""
categories.py - which category an expense or income belongs to.

EXPENSE categories are the team's existing ones from
src/expense_categorization/rules.py (KEYWORD_RULES): Utilities, Transport,
Groceries, Dining, Entertainment, Health, Education, Housing, Shopping, Other.
This file only ADDS Roman Urdu / Urdu words for those same categories, and
falls back to the team's own English rule_based_predict() - no second,
competing category list.

INCOME categories do not exist in the repo yet, so the list below is a
PROPOSAL (pending team lead / product confirmation). Users can always type
their own category; it is kept as they wrote it.
"""
import re

from ...expense_categorization.rules import KEYWORD_RULES, rule_based_predict

EXPENSE_CATEGORIES: list[str] = [name for name, _ in KEYWORD_RULES]

# Roman Urdu / Urdu words for the team's existing expense categories.
EXPENSE_WORDS_UR: dict[str, list[str]] = {
    "Utilities": ["bijli", "bijli ka bill", "gas ka bill", "sui gas", "pani ka bill", "internet", "wifi", "bill",
                  "بجلی", "بل", "گیس"],
    "Transport": ["petrol", "diesel", "cng", "rickshaw", "bykea", "careem", "kiraya gaari", "gaari", "bike",
                  "پٹرول", "کرایہ گاڑی"],
    "Groceries": ["sabzi", "doodh", "anday", "aata", "cheeni", "ration", "sauda", "kiryana", "سبزی", "راشن"],
    "Dining": ["khana", "chai", "lunch", "dinner", "nashta", "biryani", "hotel", "کھانا", "چائے"],
    "Health": ["dawai", "dawa", "doctor", "hospital", "dawakhana", "دوائی", "ڈاکٹر"],
    "Education": ["school", "fees", "fee", "tuition", "kitaben", "اسکول", "فیس"],
    "Housing": ["rent", "kiraya", "kiraye", "makaan", "furniture", "marammat", "کرایہ"],
    "Shopping": ["kapray", "kapde", "joote", "shopping", "کپڑے"],
    "Entertainment": ["movie", "film", "cinema", "netflix", "فلم"],
}

INCOME_CATEGORIES: dict[str, list[str]] = {   # PROPOSED - see module docstring
    "Sales": ["sale", "sales", "becha", "bechi", "beche", "bika", "biki", "bikri", "order", "orders", "فروخت", "بیچا"],
    "Services": ["service", "services", "consultation", "installation", "job", "kaam"],
    "Customer Payment Received": ["udhaar wapas", "wapas", "wapis", "payment received", "wasool", "wasooli",
                                  "recovery", "وصول"],
    "Salary / Wages Received": ["salary", "tankhwah", "tankhah", "تنخواہ"],
    "Other Income": ["commission", "interest", "bonus", "gift", "profit"],
}


def match_category(text: str, direction: str | None) -> str | None:
    lowered = f" {text.lower()} "
    best: tuple[int, str] | None = None
    tables = []
    if direction in (None, "expense"):
        tables.append(EXPENSE_WORDS_UR)
    if direction in (None, "income"):
        tables.append(INCOME_CATEGORIES)
    for table in tables:
        for name, words in table.items():
            for w in [*words, name.lower()]:
                if _contains_word(lowered, w) and (best is None or len(w) > best[0]):
                    best = (len(w), name)
    if best:
        return best[1]
    if direction in (None, "expense"):
        hit = rule_based_predict(text, None)          # the team's English keyword rules
        if hit and hit[0] != "Other":
            return hit[0]
        if direction == "expense":
            for name in EXPENSE_CATEGORIES:            # user typed an exact category name ("Other")
                if _contains_word(lowered, name.lower()):
                    return name
    return None


def category_names(direction: str | None) -> list[str]:
    if direction == "income":
        return list(INCOME_CATEGORIES)
    if direction == "expense":
        return EXPENSE_CATEGORIES
    return [*EXPENSE_CATEGORIES, *INCOME_CATEGORIES]


def _contains_word(haystack: str, word: str) -> bool:
    if re.search(r"[؀-ۿ]", word):
        return word in haystack
    return re.search(rf"(?<![a-z]){re.escape(word.lower())}(?![a-z])", haystack) is not None
