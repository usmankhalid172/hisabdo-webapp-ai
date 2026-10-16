"""INTENT-xx / SLOT-xx: intent recognition and slot extraction (English, Roman Urdu, Urdu).

Run from the repo root:  pytest tests/test_dialogue_intents.py -v
"""
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from src.financial_assistant.dialogue import extract
from src.financial_assistant.dialogue.models import Intent, Language
from src.financial_assistant.dialogue.recognizer import RuleBasedIntentRecognizer

TODAY = date(2026, 10, 14)
DATA = Path(__file__).resolve().parents[1] / "data"
R = RuleBasedIntentRecognizer()


def intent_of(text):
    return R.recognize(text, TODAY).intent


@pytest.mark.parametrize("case", json.loads((DATA / "intent_eval_cases.json").read_text(encoding="utf-8"))["cases"],
                         ids=lambda c: c["text"][:30])
def test_INTENT_01_labelled_set(case):
    assert intent_of(case["text"]).value == case["intent"]


def test_INTENT_02_heldout_set_accuracy_is_at_least_85_percent():
    """Held-out messages were NOT used to write the rules. Current result: 30/33."""
    cases = json.loads((DATA / "intent_eval_cases_heldout.json").read_text(encoding="utf-8"))["cases"]
    correct = sum(intent_of(c["text"]).value == c["intent"] for c in cases)
    assert correct / len(cases) >= 0.85


@pytest.mark.parametrize("text", ["mera balance kitna hai?", "What is my balance?", "میرا بیلنس کتنا ہے؟",
                                  "is mahine ki report dikhao", "How much did I spend last month?"])
def test_INTENT_03_private_questions_never_classified_as_faq(text):
    assert intent_of(text) in (Intent.ACCOUNT_QUERY, Intent.REPORT)


def test_INTENT_04_money_without_direction_is_flagged_unclear():
    result = R.recognize("500", TODAY)
    assert result.intent == Intent.ADD_EXPENSE and "amount_only" in result.signals and result.confidence < 0.5


def test_INTENT_05_expense_and_income_cues_together_is_unclear():
    result = R.recognize("500 diye aur 500 mile", TODAY)   # two directions, same amount
    assert "direction_unclear" in result.signals or result.slots.amount is None


@pytest.mark.parametrize("text, amount", [
    ("Aaj 500 ka petrol dala", "500.00"), ("Rs 1,500 rent", "1500.00"), ("2k ka saman", "2000.00"),
    ("1.5 lakh ka maal", "150000.00"), ("10 hazar mile", "10000.00"), ("۵۰۰ روپے", "500.00"),
    ("PKR 2,50,000 sale", "250000.00"), ("paid 99.50 for tea", "99.50"),
    ("15 October ko 3000 diye", "3000.00"), ("12/10 ko 800 ka bill", "800.00"),
])
def test_SLOT_01_amounts(text, amount):
    assert extract.extract_amount(text) == Decimal(amount)


@pytest.mark.parametrize("text", ["2 cheezen 300 aur 400", "kal kharcha kiya", "15 October", "0 rupay"])
def test_SLOT_02_no_amount_or_two_different_amounts_means_ask(text):
    assert extract.extract_amount(text) is None


@pytest.mark.parametrize("text, expected", [
    ("aaj", TODAY), ("today", TODAY), ("kal", date(2026, 10, 13)), ("yesterday", date(2026, 10, 13)),
    ("parson", date(2026, 10, 12)), ("12/10", date(2026, 10, 12)), ("3 October", date(2026, 10, 3)),
    ("Sep 30", date(2026, 9, 30)), ("5 tareekh", date(2026, 10, 5)), ("آج", TODAY), ("31/02", None),
])
def test_SLOT_03_dates(text, expected):
    assert extract.extract_date(text, TODAY) == expected


@pytest.mark.parametrize("text, label, start", [
    ("is mahine", "October 2026", date(2026, 10, 1)), ("last month", "September 2026", date(2026, 9, 1)),
    ("pichle mahine", "September 2026", date(2026, 9, 1)), ("September", "September 2026", date(2026, 9, 1)),
    ("November", "November 2025", date(2025, 11, 1)),   # a later month name means last year
    ("is saal", "2026", date(2026, 1, 1)),
])
def test_SLOT_04_report_periods(text, label, start):
    period = extract.extract_period(text, TODAY)
    assert period.label == label and period.start == start


@pytest.mark.parametrize("text, currency", [("Rs 500", "PKR"), ("500 rupay", "PKR"), ("$20", "USD"),
                                            ("50 dirham", "AED"), ("500", None)])
def test_SLOT_05_currency_only_when_said(text, currency):
    assert extract.extract_currency(text) == currency


@pytest.mark.parametrize("text, name", [("Ali ko 500 diye", "Ali"), ("bilal se 2000 mile", "Bilal"),
                                        ("paid 500 to Sara", "Sara"), ("15 October ko 300", None),
                                        ("petrol ko 500", None)])
def test_SLOT_06_counterparty(text, name):
    assert extract.extract_counterparty(text) == name


@pytest.mark.parametrize("text, language", [("Aaj 500 ka petrol dala", Language.ROMAN_URDU),
                                            ("I paid 500 for petrol", Language.ENGLISH),
                                            ("آج 500 کا پٹرول", Language.ROMAN_URDU)])
def test_SLOT_07_language(text, language):
    assert extract.detect_language(text) == language


@pytest.mark.parametrize("text, yes, no", [("haan", True, False), ("ji", True, False), ("yes", True, False),
                                           ("theek hai", True, False), ("nahi", False, True), ("cancel", False, True),
                                           ("haan 600", False, False), ("nahi 600 tha", False, True)])
def test_SLOT_08_yes_no(text, yes, no):
    assert extract.is_yes(text) is yes and extract.is_no(text) is no


def test_SLOT_09_categories_use_the_teams_existing_category_names():
    from src.expense_categorization.rules import KEYWORD_RULES
    official = {name for name, _ in KEYWORD_RULES}
    for text, expected in [("bijli ka bill 3500 bhara", "Utilities"), ("Aaj 500 ka petrol dala", "Transport"),
                           ("kiraya 20000 diya", "Housing"), ("dawai 900 ki li", "Health"),
                           ("I paid 1200 for the electricity bill", "Utilities"),   # team's English rules
                           ("spent 300 at KFC", "Dining")]:
        category = R.recognize(text, TODAY).slots.category
        assert category == expected and category in official, text
    assert R.recognize("Aaj 3000 ki sale hui", TODAY).slots.category == "Sales"
    assert R.recognize("Ali ko 500 diye", TODAY).slots.category is None   # unknown -> the flow asks
