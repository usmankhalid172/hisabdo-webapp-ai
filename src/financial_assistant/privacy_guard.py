"""
privacy_guard.py - does a message ask for SOMEONE ELSE's financial data?

Used by service.handle_chat() BEFORE anything else (router, backend, RAG, LLM).
A match is refused deterministically, so no prompt-injection can talk around it.

Day-7 evaluation root causes fixed here (see docs/dept3-chatbot-evaluation-and-fixes.md):
  * PRIVACY GAP: Roman Urdu / Urdu requests ("Ali ka balance kitna hai?",
    "mere bhai ka kharcha batao", "uska balance", "علی کا بیلنس") were not detected.
    They reached the backend path, which answers with the *requester's own* figures
    as if they were Ali's - wrong answer and a privacy-boundary failure.
  * FALSE REFUSALS: the old English patterns made the apostrophe optional
    (r"customer'?s", r"other user'?s"), so plurals in ordinary questions
    ("how much each customer owes", "shown to other users?") were refused.
    Possessives now need a real apostrophe; plurals only count in explicit
    data requests ("all users' balances", "other users' data").
"""
from __future__ import annotations

import re
from functools import lru_cache

APOS = r"(?:'s|’s|s'|s’)"   # friend's / friends'

# ------------------------------------------------------------------ English
RELATION_WORDS = (
    r"friend|colleague|coworker|co-worker|wife|husband|spouse|partner|boyfriend|girlfriend|brother|sister|"
    r"mother|father|mom|mum|dad|boss|manager|client|customer|employee|roommate|teammate|neighbou?r|son|daughter|"
    r"cousin|uncle|aunt|person|user|someone else|somebody else|other person|another person|other user|another user"
)
EN_RELATION_POSSESSIVE = re.compile(rf"\b(?:{RELATION_WORDS}){APOS}", re.I)
EN_PRONOUNS = re.compile(r"\b(his|her|their)\b\s+(?:\w+\s+){0,2}?"
                         r"(balance|expenses?|spending|income|revenue|profit|outstanding|account|data|"
                         r"transactions?|records?|salary|payments?|money)\b", re.I)
EN_EVERYONE = re.compile(r"\b(all|every|other|another)\s+(users?|customers?|accounts?|people)(?:'|’)?s?\s+"
                         r"(?:\w+\s+){0,1}?(balances?|expenses?|data|records?|accounts?|income|revenue|transactions?)\b"
                         r"|\beveryone(?:'s|’s)\b", re.I)
EN_OF_RELATION = re.compile(rf"\b(balance|expenses?|spending|income|revenue|profit|outstanding|account|data|"
                            rf"transactions?|records?|salary|sales)\s+of\s+(?:my|his|her|their|our|the|a|an)?\s*"
                            rf"(?:\w+\s+)?(?:{RELATION_WORDS})\b", re.I)
EN_CONCEPT = re.compile(r"^\s*(does|do|can|will|would|should|why|how do|how does|how can)\b", re.I)
ID_REFERENCE = re.compile(r"\b(user|account|customer|client)\s*(?:#|no\.?|number)?\s*\d+\b", re.I)
_SAFE_POSSESSIVE_WORDS = {"my", "this", "that", "today's", "month's", "week's", "year's", "quarter's", "day's",
                          "account's", "app's", "system's", "hisabdo's", "business's", "company's", "shop's"}

# ------------------------------------------------------------------ Roman Urdu
FIN_RU = (r"balance|kharcha|kharche|kharch|expenses?|income|aamdani|amdani|revenue|profit|munafa|data|account|"
          r"hisaab|hisab|outstanding|udhaar|udhar|salary|tankhwah|tankhah|paise|paisay|transactions?|records?|"
          r"bachat|baqaya|baqi|sales?|spending")
RU_OWN = {"mera", "meri", "mere", "apna", "apni", "apne", "hamara", "hamari", "hamare", "humara", "humari",
          "humare", "is", "iss", "us", "uss", "mahine", "mahina", "month", "aaj", "kal", "saal", "hafte", "week",
          "din", "business", "dukaan", "dukan", "shop", "company", "app", "hisabdo", "har", "kis", "kisi", "total",
          "pichle", "pichla", "agle", "category", "expense", "is mahine", "cash", "january", "february", "march",
          "april", "may", "june", "july", "august", "september", "october", "november", "december"}
RU_THIRD_PRONOUNS = re.compile(rf"\b(uska|uski|uske|unka|unki|unke|iska|iski|iske|inka|inki|inke|unhon|uss\s+ka)\b"
                               rf"\s+(?:\w+\s+){{0,2}}?({FIN_RU})\b", re.I)
RU_RELATIONS = re.compile(rf"\b(bhai|bhaiyya|behen|behan|bhen|dost|dosto|abbu|ammi|walid|walida|biwi|begum|shohar|"
                          rf"miyan|beta|beti|chacha|chachi|mamu|khala|phupho|saathi|padosi|rishtedar|boss|"
                          rf"husband|wife|friend|colleague|employee|naukar)\b\s+(?:\w+\s+){{0,1}}?(ka|ki|ke)\b", re.I)
RU_OTHERS = re.compile(r"\b(doosre|dusre|doosri|dusri|kisi\s+aur|dusron|doosron|sab\s+users?|sabhi|tamam)\b"
                       r"\s+(?:\w+\s+){0,2}?(user|users|bande|logon|log|shakhs|account|accounts|customer|ka|ki|ke)\b", re.I)
RU_NAME_POSSESSIVE = re.compile(rf"\b([a-z]{{3,15}})\s+(ka|ki|ke)\s+(?:\w+\s+){{0,1}}?({FIN_RU})\b", re.I)
GENERIC_QUESTION = re.compile(r"\b(kyun|kyon|kyu|why|kya\s+hota|kya\s+hoti|kya\s+hai\s+matlab|matlab|meaning|"
                              r"how\s+to|kaise\s+track|track\s+karna|zaroori|important|tips?)\b", re.I)
REQUEST_WORDS = re.compile(r"\b(kitna|kitni|kitne|batao|bataen|bataiye|dikhao|dikhaen|dikhaiye|show|tell|give|kya|"
                           r"what\s+is|what's|how\s+much|chahiye|send)\b", re.I)

# ------------------------------------------------------------------ Urdu script
FIN_UR = r"(بیلنس|خرچ|خرچہ|اخراجات|آمدنی|حساب|ڈیٹا|اکاؤنٹ|منافع|ادھار|تنخواہ|پیسے)"
UR_OWN = {"میرا", "میری", "میرے", "اپنا", "اپنی", "اپنے", "ہمارا", "ہماری", "ہمارے", "مہینے", "آج", "کل", "سال", "کاروبار", "دکان"}
UR_POSSESSIVE = re.compile(rf"(\S+)\s+(کا|کی|کے)\s+(?:\S+\s+)?{FIN_UR}")
UR_THIRD = re.compile(rf"(اس|ان|دوسرے|دوسری|بھائی|بہن|دوست|والد|والدہ|بیوی|شوہر)\s+(کا|کی|کے)\s+(?:\S+\s+)?{FIN_UR}")


def mentions_third_party(message: str) -> bool:
    """True if the message asks about another person's financial data (any supported language)."""
    text = " ".join(message.split())
    lowered = text.lower()

    # English
    if EN_RELATION_POSSESSIVE.search(text) or EN_EVERYONE.search(text) or ID_REFERENCE.search(text):
        return True
    if EN_OF_RELATION.search(text):
        return True
    # "Show me their expenses" is a request; "Does HisabDo help freelancers track their income?" is not.
    if EN_PRONOUNS.search(text) and not EN_CONCEPT.search(text):
        return True
    if _bare_name_possessive(text):
        return True

    # Roman Urdu
    if RU_THIRD_PRONOUNS.search(lowered) or RU_OTHERS.search(lowered):
        return True
    asks = bool(REQUEST_WORDS.search(lowered) or "?" in text or "؟" in text)
    if RU_RELATIONS.search(lowered) and re.search(FIN_RU, lowered) and asks:
        return True
    for m in RU_NAME_POSSESSIVE.finditer(lowered) if asks else ():   # "sabzi ka kharcha 500" is an entry, not a request
        owner = m.group(1)
        if re.fullmatch(FIN_RU, owner):
            continue             # "meri expenses ka data" - the owner word is itself a finance word
        if owner in RU_OWN or owner in _category_words() or owner in {"customer", "customers", "supplier", "business"}:
            if owner.startswith("customer") and REQUEST_WORDS.search(lowered) and not GENERIC_QUESTION.search(lowered):
                return True      # "customer ka balance batao" = a specific customer's data request
            continue
        if GENERIC_QUESTION.search(lowered) and not REQUEST_WORDS.search(lowered):
            continue             # "profit ka matlab kya hai?" is a concept question
        return True

    # Urdu script
    asks_ur = asks or bool(re.search(r"کتنا|کتنی|کتنے|دکھائیں|دکھاؤ|بتائیں|بتاؤ|کیا ہے", text))
    if UR_THIRD.search(text) and asks_ur:
        return True
    for m in UR_POSSESSIVE.finditer(text) if asks_ur else ():
        if m.group(1) not in UR_OWN:
            return True
    return False


def _bare_name_possessive(message: str) -> bool:
    """'What is Ali's balance?' - a capitalised word (not the first) followed by 's."""
    words = message.split()
    for i, word in enumerate(words):
        if i == 0:
            continue
        stripped = word.rstrip(",.?!")
        if re.fullmatch(r"[A-Z][a-zA-Z]*(?:'s|’s)", stripped) and stripped.lower() not in _SAFE_POSSESSIVE_WORDS:
            return True
    return False


@lru_cache
def _category_words() -> frozenset[str]:
    """Expense/income words ("petrol ka kharcha", "sabzi ka kharcha") are things, not people."""
    from ..expense_categorization.rules import KEYWORD_RULES
    from .dialogue.categories import EXPENSE_WORDS_UR, INCOME_CATEGORIES
    words: set[str] = set()
    for _, keywords in KEYWORD_RULES:
        words.update(w for k in keywords for w in k.split())
    for table in (EXPENSE_WORDS_UR, INCOME_CATEGORIES):
        for name, keywords in table.items():
            words.update(w.lower() for k in [name, *keywords] for w in k.split())
    words.update({"bill", "maal", "saman", "samaan", "stock", "staff", "mazdoor", "order", "orders", "rent",
                  "kiraye", "dawai", "fees", "gaari", "bijli", "gas", "pani", "internet", "mobile", "khane"})
    return frozenset(words)
