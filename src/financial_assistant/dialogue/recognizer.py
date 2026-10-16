"""
recognizer.py - work out the user's intent from one message.

Rule-based: each intent has cue words in English, Roman Urdu and Urdu. Every cue
that appears adds to that intent's score; an amount in the message makes the
money intents more likely. The winner must beat the runner-up clearly, otherwise
we treat it as unclear and ask (never guess with money).

Why rules and not the AI model?  The decision "is this an expense or income?"
must be predictable, testable and free. An LLM-based recognizer can be added
later behind the same IntentRecognizer interface and compared on the same tests.
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import date

from . import extract
from .categories import match_category
from .models import Intent, IntentResult, Slots

CUES: dict[Intent, list[str]] = {
    Intent.ADD_EXPENSE: [
        "kharcha", "kharch", "kharche", "expense", "spent", "spend", "paid", "pay kiya", "pay kiye", "payment ki",
        "diye", "diya", "di", "de diye", "kharida", "kharidi", "kharide", "bought", "buy", "bill bhara", "bhara",
        "dala", "dalwaya", "lagaye", "lagaya", "laga", "purchase", "add expense", "خرچ", "خرچہ", "دیے", "دیئے",
        "خریدا", "ادا",
    ],
    Intent.ADD_INCOME: [
        "income", "aamdani", "amdani", "mile", "mila", "mili", "received", "receive", "got paid", "aaye", "aye",
        "aya", "aaya", "kamaye", "kamaya", "earned", "sale hui", "sale ki", "becha", "bechi", "beche", "bika", "biki",
        "wasool", "wasooli", "jama", "deposit", "add income", "آمدنی", "ملے", "ملا", "وصول", "بیچا",
    ],
    Intent.CORRECT_TRANSACTION: [
        "galat", "ghalat", "wrong", "mistake", "correct", "correction", "change", "badal", "badlo", "update",
        "edit", "theek karo", "thik karo", "theek kar do", "fix", "delete", "hata do", "hatao", "remove",
        "nahi tha", "nahi thi", "instead", "last entry", "last wali", "pichli entry", "pichhli entry",
        "previous entry", "wali entry", "entry ko", "entry mein", "pichli wali", "غلط", "تبدیل", "ہٹا",
    ],
    Intent.CATEGORIZE: [
        "category", "categorize", "categorise", "categories", "classify", "kis category", "head mein", "mein daal",
        "mein dalo", "zumray", "زمرہ", "کیٹیگری",
    ],
    Intent.REPORT: [
        "report", "summary", "my statement", "mera statement", "breakdown", "total spending", "my spending",
        "spending this month", "spending for", "hisaab dikhao", "hisab dikhao", "total kitna",
        "kitna kharcha", "kitna kharch", "kharcha kitna", "kharch kitna", "kitni sale", "sale kitni", "kitni income",
        "income kitni", "kitna hua", "kitni hui", "how much did i spend", "how much did i earn", "how much did i make",
        "total sales", "my sales", "meri sales", "sales kitni", "business earn", "did my business earn",
        "profit kitna", "munafa", "profit and loss", "p&l", "رپورٹ", "خلاصہ",
    ],
    Intent.ACCOUNT_QUERY: [
        "balance", "mera balance", "my balance", "account mein kitne", "kitne paise", "how much money do i have",
        "how much money do i currently have", "money do i have", "money i have",
        "cash in hand", "bachat", "baqaya", "baqi", "remaining", "outstanding", "mere account", "my account",
        "بیلنس", "بقایا",
    ],
    Intent.FAQ: [
        "hisabdo", "hisab do", "app", "feature", "features", "kya aap", "can you", "can the", "do you", "does the",
        "how do i", "how to", "kaise karte", "kaise karun", "kaise kare", "support", "language", "urdu", "help",
        "kya hai", "what is", "kon si", "which", "حساب دو", "ایپ",
    ],
    Intent.GREETING: ["hi", "hello", "hey", "salam", "assalam", "aoa", "assalamualaikum", "good morning", "السلام"],
}

STRONG = {  # cues that decide on their own (no amount needed)
    Intent.REPORT: 2.0, Intent.ACCOUNT_QUERY: 2.0, Intent.CORRECT_TRANSACTION: 1.5, Intent.CATEGORIZE: 1.5,
}


class IntentRecognizer(ABC):
    @abstractmethod
    def recognize(self, message: str, today: date) -> IntentResult: ...


class RuleBasedIntentRecognizer(IntentRecognizer):
    MIN_CONFIDENCE = 0.5

    def recognize(self, message: str, today: date) -> IntentResult:
        text = extract.normalise(message)
        lowered = f" {text.lower()} "
        language = extract.detect_language(text)
        amount = extract.extract_amount(text)

        if extract.is_yes(text):
            return IntentResult(intent=Intent.CONFIRM, confidence=1.0, language=language, signals=["yes"])
        if extract.is_no(text) and amount is None and len(text.split()) <= 4:
            return IntentResult(intent=Intent.DENY, confidence=1.0, language=language, signals=["no"])

        scores: dict[Intent, float] = {}
        signals: list[str] = []
        for intent, cues in CUES.items():
            for cue in cues:
                if _has(lowered, cue):
                    scores[intent] = scores.get(intent, 0.0) + STRONG.get(intent, 1.0)
                    signals.append(f"{intent.value}:{cue}")
        if amount is not None:
            for money_intent in (Intent.ADD_EXPENSE, Intent.ADD_INCOME, Intent.CORRECT_TRANSACTION):
                if money_intent in scores:
                    scores[money_intent] += 1.0
            signals.append("amount")

        # Private questions about "my" numbers are account queries even with report-like words.
        if re.search(r"\b(mera|meri|mere|my|mujhe)\b|میرا|میری", lowered) and Intent.FAQ in scores \
                and (Intent.ACCOUNT_QUERY in scores or Intent.REPORT in scores):
            scores.pop(Intent.FAQ)

        # "What is a cash flow statement?" asks about a CONCEPT, not the user's own figures.
        possessive = re.search(r"\b(mera|meri|mere|my|mujhe|i|hum|hamara|hamari)\b|میرا|میری", lowered)
        if not possessive and re.search(r"\b(what is|what's|what are|kya hai|kya hota|kya hoti|matlab|meaning)\b", lowered):
            for private in (Intent.REPORT, Intent.ACCOUNT_QUERY):
                scores.pop(private, None)
            scores.setdefault(Intent.FAQ, 1.0)

        # "How much revenue did I make?" / "how much profit do I have" = the user's own figures.
        if re.search(r"\bhow much\s+(revenue|income|profit|money|sales|expenses?|spending)\s+(did|do|have)\s+i\b", lowered):
            scores[Intent.REPORT] = scores.get(Intent.REPORT, 0.0) + 2.0
            scores.pop(Intent.FAQ, None)

        # Yes/no and "why/which" questions ABOUT the product ("Is my balance shared with...?",
        # "Which report shows...?", "Munafa ke bawajood cash kam kyun hota hai?") are not requests for
        # the user's figures. Private routes need an actual data request (how much / show / batao ...).
        data_request = re.search(r"\b(how much|how many|what('s| is| are) my|show|tell me|give me|kitna|kitni|kitne|"
                                 r"dikhao|dikhaen|batao|bataen|report do|total|balance\?|summary)\b", lowered)
        concept = re.search(r"^\s*(is|does|do|can|will|would|which|why|should)\b|\b(kyun|kyon|why|which report|"
                            r"shared|unsure|not sure|confident|automatically|bawajood)\b", lowered)
        if concept and not data_request and ({Intent.REPORT, Intent.ACCOUNT_QUERY} & scores.keys()):
            for private in (Intent.REPORT, Intent.ACCOUNT_QUERY):
                scores.pop(private, None)
            scores.setdefault(Intent.FAQ, 1.0)

        # "Can I download my spending as a spreadsheet?" asks HOW TO use a feature, not for figures.
        if amount is None and ({Intent.REPORT, Intent.ACCOUNT_QUERY} & scores.keys()) \
                and not re.search(r"\bhow much\b|kitna|kitni|kitne", lowered) and re.search(
                r"\b(export|download|spreadsheet|csv|pdf|excel|how do i|how can i|can i|kaise)\b", lowered):
            for private in (Intent.REPORT, Intent.ACCOUNT_QUERY):
                scores.pop(private, None)
            scores.setdefault(Intent.FAQ, 1.0)

        # A question mark with no money words and no amount is most likely a general/product question.
        is_question = "?" in text or "؟" in text
        if is_question and amount is None and not ({Intent.REPORT, Intent.ACCOUNT_QUERY} & scores.keys()):
            scores.pop(Intent.ADD_EXPENSE, None)
            scores.pop(Intent.ADD_INCOME, None)
            if not scores:
                scores[Intent.GENERAL] = 1.0

        slots = Slots(
            amount=amount,
            currency=extract.extract_currency(text),
            date=extract.extract_date(text, today),
            counterparty=extract.extract_counterparty(text),
            period=extract.extract_period(text, today),
        )

        if not scores:
            intent = Intent.GENERAL
            if amount is not None:          # "500 petrol" - money, but which way? ask.
                intent = Intent.ADD_EXPENSE if match_category(text, "expense") else Intent.GENERAL
                if intent == Intent.GENERAL:
                    return IntentResult(intent=Intent.ADD_EXPENSE, confidence=0.4, slots=_with_unknown_direction(slots, text),
                                        language=language, signals=["amount_only"])
            return IntentResult(intent=intent, confidence=0.5 if intent != Intent.GENERAL else 0.3,
                                slots=_with_category(slots, text, intent), language=language, signals=signals or ["none"])

        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        best, best_score = ranked[0]
        runner_up = ranked[1][1] if len(ranked) > 1 else 0.0

        # Expense vs income tie with an amount: we know it's money, not which way -> ask the direction.
        if {Intent.ADD_EXPENSE, Intent.ADD_INCOME} <= scores.keys() and \
                abs(scores[Intent.ADD_EXPENSE] - scores[Intent.ADD_INCOME]) < 1.0 and best in (Intent.ADD_EXPENSE, Intent.ADD_INCOME):
            return IntentResult(intent=Intent.ADD_EXPENSE, confidence=0.4, slots=_with_unknown_direction(slots, text),
                                language=language, signals=[*signals, "direction_unclear"])

        confidence = best_score / (best_score + runner_up) if best_score + runner_up else 0.0
        return IntentResult(intent=best, confidence=round(confidence, 2), slots=_with_category(slots, text, best),
                            language=language, signals=signals)


def _has(lowered: str, cue: str) -> bool:
    if re.search(r"[؀-ۿ]", cue):
        return cue in lowered
    return re.search(rf"(?<![a-z]){re.escape(cue)}(?![a-z])", lowered) is not None


def _with_category(slots: Slots, text: str, intent: Intent) -> Slots:
    if intent != Intent.REPORT:
        slots.period = None                       # periods only matter for reports
    direction = {Intent.ADD_EXPENSE: "expense", Intent.ADD_INCOME: "income"}.get(intent)
    slots.category = match_category(text, direction)
    if intent == Intent.REPORT:
        lowered = text.lower()
        if re.search(r"kharch|expense|spend|spent|خرچ", lowered):
            slots.report_type = "expense"
        elif re.search(r"income|aamdani|amdani|sale|earn|آمدنی", lowered):
            slots.report_type = "income"
    return slots


def _with_unknown_direction(slots: Slots, text: str) -> Slots:
    slots.direction, slots.period = None, None
    slots.category = match_category(text, None)
    return slots
