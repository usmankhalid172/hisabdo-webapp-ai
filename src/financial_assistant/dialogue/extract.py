"""
extract.py - pull structured values (slots) out of a message.

Works for English, Roman Urdu and Urdu script. Rule-based on purpose:
predictable, fast, free, and easy to test. It never guesses an amount:
if no clear number is found, the flow asks for it.
"""
from __future__ import annotations

import calendar
import re
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from .models import Language, Period

URDU_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

ROMAN_URDU_MARKERS = {
    "kya", "kia", "hai", "hain", "ka", "ki", "ke", "ko", "se", "sy", "mein", "main", "mai", "aaj", "kal", "diye",
    "diya", "mile", "mila", "karo", "kar", "kardo", "nahi", "nai", "haan", "han", "ji", "mera", "meri", "mere",
    "kitna", "kitne", "kaise", "kaisa", "tha", "thi", "hua", "hui", "wala", "wali", "dala", "liye", "lia", "liya",
    "rupay", "rupaye", "hazar", "hazaar", "kharcha", "kharch", "becha", "dikhao", "batao", "abhi", "pichle", "is",
    "do", "wapas", "bhi", "aur", "ya", "tou", "to", "yeh", "ye", "woh", "wo",
}
ENGLISH_MARKERS = {"the", "what", "how", "is", "my", "i", "paid", "spent", "received", "show", "please", "for",
                   "to", "from", "of", "and", "did", "was", "this", "last", "today", "yesterday", "add", "change"}

MONTHS = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
MONTHS.update({m.lower(): i for i, m in enumerate(calendar.month_abbr) if m})
MONTHS.update({"sept": 9})

_WORD = re.compile(r"[a-z]+")
_NUMBER = re.compile(
    r"(?<![\w.])(?:(rs\.?|pkr|usd|aed|\$)\s*)?(\d{1,3}(?:,\d{2,3})+|\d+(?:\.\d+)?)\s*"
    r"(k\b|hazar\b|hazaar\b|thousand\b|lakh\b|lac\b|lacs\b|lakhs\b|crore\b|million\b)?",
    re.IGNORECASE,
)
_MULTIPLIER = {"k": 1_000, "hazar": 1_000, "hazaar": 1_000, "thousand": 1_000, "lakh": 100_000, "lac": 100_000,
               "lacs": 100_000, "lakhs": 100_000, "crore": 10_000_000, "million": 1_000_000}
_DATE_AFTER = re.compile(r"^\s*(tareekh|tarikh|tarik|date|th|st|nd|rd|ko\s+(?:" + "|".join(MONTHS) + r"))\b", re.I)
_CURRENCY_WORDS = [
    (re.compile(r"\b(rs\.?|pkr|rupees?|rupay|rupaye|rupe|rupiya)\b|روپے|روپیہ", re.I), "PKR"),
    (re.compile(r"\$|\b(usd|dollars?)\b", re.I), "USD"),
    (re.compile(r"\b(aed|dirhams?)\b", re.I), "AED"),
]


def normalise(text: str) -> str:
    return " ".join(text.translate(URDU_DIGITS).split())


def detect_language(text: str) -> Language:
    if re.search(r"[؀-ۿ]", text):
        return Language.ROMAN_URDU          # Urdu script -> reply in Roman Urdu (HisabDo prompt rule)
    words = _WORD.findall(text.lower())
    roman = sum(w in ROMAN_URDU_MARKERS for w in words)
    english = sum(w in ENGLISH_MARKERS for w in words)
    return Language.ROMAN_URDU if roman > english else Language.ENGLISH


def extract_amount(text: str) -> Decimal | None:
    """The transaction amount, or None if there is no clear one. Numbers that are dates are skipped."""
    text = normalise(text)
    candidates: list[tuple[int, Decimal]] = []
    for m in _NUMBER.finditer(text):
        prefix, number, multiplier = m.group(1), m.group(2), m.group(3)
        after = text[m.end():]
        if _DATE_AFTER.match(after) or _is_part_of_date(text, m.start(), m.end()):
            continue
        try:
            value = Decimal(number.replace(",", ""))
        except InvalidOperation:
            continue
        if multiplier:
            value *= _MULTIPLIER[multiplier.lower()]
        if value <= 0:
            continue
        has_money_word = bool(prefix or multiplier or re.match(r"\s*(rs\.?|pkr|rupees?|rupay|rupaye|روپے|ka|ki|ke)\b", after, re.I))
        candidates.append((2 if has_money_word else 1, value))
    if not candidates:
        return None
    best_rank = max(r for r, _ in candidates)
    best = [v for r, v in candidates if r == best_rank]
    if len(set(best)) != 1:
        return None                                     # two different clear amounts -> ask, don't guess
    return best[0].quantize(Decimal("0.01"))


def _is_part_of_date(text: str, start: int, end: int) -> bool:
    before, after = text[max(0, start - 12):start].lower(), text[end:end + 12].lower()
    if re.match(r"^[/-]\d", after) or re.search(r"\d[/-]$", before):
        return True
    month_next = re.match(r"^\s*([a-z]+)", after)
    month_prev = re.search(r"([a-z]+)\s*$", before)
    return bool((month_next and month_next.group(1) in MONTHS) or (month_prev and month_prev.group(1) in MONTHS))


def extract_currency(text: str) -> str | None:
    for pattern, code in _CURRENCY_WORDS:
        if pattern.search(text):
            return code
    return None


def extract_date(text: str, today: date) -> date | None:
    t = normalise(text).lower()
    if re.search(r"\b(parson|day before yesterday)\b|پرسوں", t):
        return today - timedelta(days=2)
    if re.search(r"\b(yesterday|kal|kl)\b|کل", t):
        return today - timedelta(days=1)          # past-tense money talk: "kal" = yesterday
    if re.search(r"\b(today|aaj|aj|abhi)\b|آج", t):
        return today
    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b", t)
    if m:
        day, month = int(m.group(1)), int(m.group(2))
        year = int(m.group(3)) if m.group(3) else today.year
        year = year + 2000 if year < 100 else year
        return _safe_date(year, month, day)
    m = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(" + "|".join(MONTHS) + r")\b", t) or \
        re.search(r"\b(" + "|".join(MONTHS) + r")\s+(\d{1,2})\b", t)
    if m:
        a, b = m.group(1), m.group(2)
        day, month_name = (int(a), b) if a.isdigit() else (int(b), a)
        return _safe_date(today.year, MONTHS[month_name], day)
    m = re.search(r"\b(\d{1,2})\s*(tareekh|tarikh|tarik)\b", t)
    if m:
        return _safe_date(today.year, today.month, int(m.group(1)))
    return None


def _safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def extract_period(text: str, today: date) -> Period | None:
    t = normalise(text).lower()
    first = today.replace(day=1)
    if re.search(r"\b(last|pichle|pichla|pichhle|previous)\s+(month|mahine|mahina|maheene)\b|پچھلے مہینے", t):
        end = first - timedelta(days=1)
        return Period(start=end.replace(day=1), end=end, label=end.strftime("%B %Y"))
    if re.search(r"\b(this|is|current|iss)\s+(month|mahine|mahina|maheene)\b|اس مہینے", t):
        return Period(start=first, end=_month_end(first), label=first.strftime("%B %Y"))
    if re.search(r"\b(this|is|iss)\s+(week|hafte|hafta)\b", t):
        start = today - timedelta(days=today.weekday())
        return Period(start=start, end=today, label="this week")
    if re.search(r"\b(today|aaj|aj)\b|آج", t):
        return Period(start=today, end=today, label="today")
    if re.search(r"\b(this|is|iss)\s+(year|saal)\b", t):
        return Period(start=date(today.year, 1, 1), end=date(today.year, 12, 31), label=str(today.year))
    m = re.search(r"\b(" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")\b(?:\s+(\d{4}))?", t)
    if m:
        month = MONTHS[m.group(1)]
        year = int(m.group(2)) if m.group(2) else (today.year if month <= today.month else today.year - 1)
        start = date(year, month, 1)
        return Period(start=start, end=_month_end(start), label=start.strftime("%B %Y"))
    return None


def _month_end(first: date) -> date:
    return first.replace(day=calendar.monthrange(first.year, first.month)[1])


_NOT_NAMES = {"is", "us", "un", "in", "mujhe", "hum", "main", "mein", "aap", "unhon", "kisi", "sab", "isko",
              "petrol", "bijli", "rent", "salary", "stock", "maal", "khana", "customer", "dukaan", "shop", "bank"}


def extract_counterparty(text: str) -> str | None:
    """'Ali ko 500 diye' -> Ali ; 'paid 500 to Bilal' -> Bilal. Optional slot, never asked for."""
    t = normalise(text)
    for pattern in (r"\b([A-Za-z]{3,15})\s+(?:ko|se|sy|say)\b", r"\b(?:to|from)\s+([A-Z][a-z]{2,15})\b"):
        m = re.search(pattern, t)
        if m and m.group(1).lower() not in _NOT_NAMES and m.group(1).lower() not in MONTHS:
            name = m.group(1)
            return name[0].upper() + name[1:]
    return None


YES = re.compile(r"^\s*(haan|han|haa|ha|ji|jee|ji haan|yes|y|yeah|yep|ok|okay|theek hai|thik hai|sahi|sahi hai|"
                 r"confirm|confirmed|save|save karo|save kar do|kar do|kardo|done|bilkul|ہاں|جی)\s*[.!]*\s*$", re.I)
NO = re.compile(r"\b(nahi|nai|nahin|no|nope|cancel|rehne do|rehnay do|chhoro|chorro|chodo|mat karo|stop|"
                r"band karo|نہیں|منسوخ)\b", re.I)


def is_yes(text: str) -> bool:
    return bool(YES.match(normalise(text)))


def is_no(text: str) -> bool:
    return bool(NO.search(normalise(text)))
