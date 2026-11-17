"""Conversation UX rules shared by every route (docs/dept3-conversation-ux-rulebook.md).

  U4  Human-support escalation: an account-level problem (cannot log in, account taken over, data lost after sync,
      delete the account, charges) is something only HisabDo's team can act on. The reply says so once, gives the
      verified support channels and what to include, and warns never to share a password or OTP. It runs before
      the intent router, so such a message never gets demo figures or an entry flow.
  U5  No repeated paragraphs: a reply with no citations whose long sentences the user has already seen in this
      conversation is replaced by its short follow-up form (fallbacks, boundaries, refusals).
  U6  Clarification follow-up: the answer to the "expenses" question is mapped to the option the user picked.
"""

from __future__ import annotations

import re

from .grounding.answer import TEMPLATES, detect_language

ESCALATE = re.compile(
    r"(?i)\b(can'?t|cannot|unable to|not able to)\s+(log\s?in|sign\s?in|login|access|open)\s+(to\s+)?(my\s+)?"
    r"(account|hisabdo)|\blocked out\b|\baccount\b.{0,20}\b(locked|hacked|blocked|suspended|compromised)\b|"
    r"\bhack(ed)?\b|\bsomeone else\b.{0,40}\b(logged|log(ged)? in|using|account)\b|"
    r"\b(delete|close|remove|deactivate)\s+(my\s+)?(hisabdo\s+)?account\b|"
    r"\b(data|records?|entries|khata|backup)\b.{0,30}\b(gone|lost|disappeared|vanished|missing|wiped)\b|"
    r"\b(lost|disappeared|missing)\s+(all\s+)?(my\s+)?(data|records|entries)\b|"
    r"\b(charged|refund|double charge|money deducted)\b|\bapp\b.{0,15}\b(crash(es|ing)?|not opening)\b|"
    r"login nahi|account (band|block|hack)|data (gayab|ghayab|ghaib|delete ho gaya|ud gaya)|account delete")

ESCALATION = {
    "en": ("This needs HisabDo's support team, because I can't see or change your account. Please email "
           "hisabdo.app@gmail.com or use https://hisabdo.app/contact, with the email or phone number you signed up "
           "with and a short description of what happened. Never share your password or a one-time code with anyone, "
           "including support. They aim to reply within 48 hours."),
    "roman_ur": ("Is ke liye HisabDo ki support team se rabta karna hoga, kyun ke main aap ka account dekh ya badal "
                 "nahi sakta. hisabdo.app@gmail.com par email karein ya https://hisabdo.app/contact istemal karein, "
                 "apna registered email ya phone number aur masle ki mukhtasar tafseel ke saath. Apna password ya OTP "
                 "kabhi kisi ko na batayein, support ko bhi nahi. Woh 48 ghante mein jawab dene ki koshish karte hain."),
    "ur": ("اس کے لیے حساب دو کی سپورٹ ٹیم سے رابطہ کرنا ہوگا، کیونکہ میں آپ کا اکاؤنٹ دیکھ یا تبدیل نہیں کر سکتا۔ "
           "hisabdo.app@gmail.com پر ای میل کریں یا https://hisabdo.app/contact استعمال کریں، اپنے رجسٹرڈ ای میل یا فون "
           "نمبر اور مسئلے کی مختصر تفصیل کے ساتھ۔ اپنا پاس ورڈ یا OTP کبھی کسی کو نہ بتائیں، سپورٹ کو بھی نہیں۔ وہ 48 "
           "گھنٹے میں جواب دینے کی کوشش کرتے ہیں۔"),
}

# U5: short follow-up forms, used when the full text was already shown in this conversation
REPEAT = {
    "en": {"fallback": "That one isn't in HisabDo's help pages either. Support at hisabdo.app@gmail.com can help with "
                       "anything the pages don't cover.",
           "boundary": "That's outside what I can help with here. Ask me about your entries, reports or a HisabDo "
                       "feature.",
           "escalation": "Support at hisabdo.app@gmail.com is the right place for this too."},
    "roman_ur": {"fallback": "Yeh bhi HisabDo ke help pages mein nahi hai. Jo baat pages mein na ho, us ke liye "
                             "support (hisabdo.app@gmail.com) madad kar sakti hai.",
                 "boundary": "Yeh meri madad ke daire se bahar hai. Apni entries, reports ya HisabDo ke kisi feature "
                             "ke baare mein poochein.",
                 "escalation": "Is ke liye bhi support (hisabdo.app@gmail.com) se rabta karein."},
    "ur": {"fallback": "یہ بھی حساب دو کے ہیلپ پیجز میں نہیں ہے۔ جو بات پیجز میں نہ ہو، اس کے لیے سپورٹ "
                       "(hisabdo.app@gmail.com) مدد کر سکتی ہے۔",
           "boundary": "یہ میری مدد کے دائرے سے باہر ہے۔ اپنی انٹریز، رپورٹس یا حساب دو کے کسی فیچر کے بارے میں پوچھیں۔",
           "escalation": "اس کے لیے بھی سپورٹ (hisabdo.app@gmail.com) سے رابطہ کریں۔"},
}

# U7 Honest limits: questions the backend contract cannot answer yet get the limit, never the overall balance
# presented as someone else's figure (D3-02, D3-03, D3-04, D3-05, D3-28). The messages are about the user's own
# account, so no third-party data is involved.
RECEIVABLES = re.compile(
    r"(?i)\b(who|which customers?|how many customers)\b.{0,40}\b(owes?|owed|still owe)\b.{0,12}\b(me|us)\b|"
    r"\bhow much (does|do|did)\s+\w+\s+owe (me|us)\b|\bwho owes me\b|\bcustomers?\b.{0,30}\bowe (me|us)\b|"
    r"\b(mera|mujhe|humein)\b.{0,40}\b(udhar|udhaar|lena|baqi|baaqi)\b.{0,40}\b(customers?|grahak)\b|"
    r"\b(customers?|grahak)\b.{0,30}\b(par|se)\b.{0,30}\b(kitna|baqi|lena)\b|"
    r"کتنا.{0,20}(ادھار|قرض).{0,20}گاہک")
PAYABLES = re.compile(r"(?i)\bhow much (do|did|must|should) i owe\b.{0,25}\b(suppliers?|vendors?)\b|"
                      r"\b(suppliers?|vendors?)\b.{0,25}\b(ko|kitna)\b.{0,15}\b(dena|dene)\b|\bwhat do i owe\b")
WEEK_FIGURES = re.compile(r"(?i)\b(how much|what|biggest|largest|total|show|kitna|kitne|kharcha)\b.{0,50}"
                          r"\b(this week|is hafte|iss hafte|is hafta|last week|pichle hafte)\b|"
                          r"\b(this week|is hafte|iss hafte)\b.{0,30}\b(kitna|kharcha|expenses?|spent)\b")
CATEGORY_BREAKDOWN = re.compile(r"(?i)\b(expenses?|kharcha|spending)\b.{0,30}\b(by|per|wise)\b.{0,3}\bcategor|"
                                r"\bcategory[- ]?wise\b|\bbreakdown\b.{0,20}\bcategor|category ke hisab")
TOTAL_WRONG = re.compile(r"(?i)\b(why is|why's|kyun|kyon)\b.{0,25}\b(total|balance|figure|number|amount)\b.{0,15}\b(wrong|incorrect|off|galat)\b|"
                         r"\b(total|balance)\b.{0,15}\b(galat|wrong|sahi nahi)\b")
ACTION_STATUS = re.compile(r"(?i)\bhave you\b.{0,12}\b(sent|paid|transferred|messaged|called|reminded|emailed)\b|"
                           r"\bdid you\b.{0,12}\b(send|pay|transfer|message|call|remind|email)\b|"
                           r"\b(aap ne|tum ne)\b.{0,25}\b(bheja|diya|kiya|bhej diya)\b")
# A capability question about the app's own documents is not a request for someone else's data (E2E-03).
PRODUCT_CAPABILITY = re.compile(r"(?i)^\s*(can i|can we|how (do|can) i|is it possible to|does hisabdo let me)\b.{0,50}"
                                r"\b(send|share|export|generate|download|email|whatsapp)\b.{0,40}"
                                r"\b(statements?|pdfs?|reports?|reminders?)\b")
FIGURE_ASK = re.compile(r"(?i)\b(balance|owes?|owed|spent|total|how much|amount|kitna|due)\b|\d")

LIMITS = {
    "en": {
        "receivables": ("I can't see per-customer or per-supplier balances yet, so I won't show you a figure that isn't "
                        "theirs. I can show your overall balance and this month's totals: ask \"What is my balance?\""),
        "week": ("I can only show the current month's figures right now, not a single week. Ask \"How much did I spend "
                 "this month?\" for the month."),
        "category": ("I can't break expenses down by category yet. I can show this month's total: ask \"How much did I "
                     "spend this month?\""),
        "total_wrong": ("Which total looks wrong, and for which period, for example this month? If one entry is wrong, "
                        "tell me which one."),
        "action": ("I can't send payments or messages, and I can't check whether one went out. I only record the "
                   "entries you tell me about."),
    },
    "roman_ur": {
        "receivables": ("Main abhi har customer ya supplier ka alag balance nahi dekh sakta, is liye aisa figure nahi "
                        "dikhaunga jo un ka na ho. Aap ka kul balance aur is mahine ke totals dikha sakta hoon: "
                        "\"Mera balance kitna hai?\" poochein."),
        "week": ("Main abhi sirf is mahine ke figures dikha sakta hoon, ek hafte ke nahi. \"Is mahine kitna kharcha "
                 "hua?\" poochein."),
        "category": ("Main abhi kharchon ko category ke hisab se alag nahi kar sakta. Is mahine ka total dikha sakta "
                     "hoon: \"Is mahine kitna kharcha hua?\""),
        "total_wrong": ("Kaun sa total galat lag raha hai, aur kis muddat ka, maslan is mahine ka? Agar koi ek entry "
                        "galat hai to batayein kaun si."),
        "action": ("Main payments ya messages nahi bhej sakta, is liye nahi bata sakta ke koi bheja gaya ya nahi. Main "
                   "sirf wohi entries likhta hoon jo aap batate hain."),
    },
}
LIMITS["ur"] = LIMITS["roman_ur"]


def honest_limit(message: str) -> str | None:
    """U7: the reply for a question the backend cannot answer yet, or an action the assistant cannot perform."""
    lang = detect_language(message)
    t = LIMITS[lang]
    if ACTION_STATUS.search(message):
        return t["action"]
    if TOTAL_WRONG.search(message):
        return t["total_wrong"]
    if RECEIVABLES.search(message) or PAYABLES.search(message):
        return t["receivables"]
    if WEEK_FIGURES.search(message):
        return t["week"]
    if CATEGORY_BREAKDOWN.search(message):
        return t["category"]
    return None


def is_product_capability(message: str) -> bool:
    return bool(PRODUCT_CAPABILITY.search(message)) and not FIGURE_ASK.search(message)


LEARN = re.compile(r"(?i)\b(how|learn|work|works|tracking|explain|kaise|samjha|batao)\b|کیسے")
TOTALS = re.compile(r"(?i)\b(total|totals|see|show|kitna|kitne|summary)\b|کتنا|ٹوٹل")


def escalation(message: str) -> str | None:
    return ESCALATION[detect_language(message)] if ESCALATE.search(message) else None


def long_sentences(text: str) -> set[str]:
    return {s.strip() for s in re.split(r"(?<=[.!?۔])\s+|\n", text) if len(s.strip()) >= 40}


def dedupe(reply: str, kind: str, earlier: list[str], message: str) -> str:
    """U5: the short form when every long sentence of this reply was already shown."""
    mine = long_sentences(reply)
    seen = set().union(*(long_sentences(e) for e in earlier)) if earlier else set()
    if mine and mine <= seen or (mine and len(mine & seen) >= max(1, len(mine) // 2) + 1):
        return REPEAT[detect_language(message)][kind]
    return reply


def follow_up(message: str, last_assistant: str | None) -> str | None:
    """U6: map the answer to the R10 expense question onto a message the routes understand."""
    if not last_assistant or last_assistant not in {t["clarify_expense"] for t in TEMPLATES.values()}:
        return None
    if LEARN.search(message):
        return "What does the HisabDo expense tracker do?"
    if TOTALS.search(message):
        return "How much did I spend this month?"
    return None
