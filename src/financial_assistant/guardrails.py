"""Safety, privacy and domain guardrails for the chatbot (docs/safety-guardrails.md).

Three layers, all deterministic (no model call, so they cannot be talked around):
  1. check_input   before the router: injection / override / prompt extraction / jailbreak, secrets, bulk or
                   personal data, unverified contacts, unsafe (fraud, evasion, hacking), toxic language,
                   self-harm, out-of-domain advice (medical, legal, investment).
  2. check_domain  on the general route: messages with nothing about HisabDo, bookkeeping or business money get a
                   boundary reply instead of free model generation.
  3. check_output  on every reply: secrets, environment values, prompt text, unverified contact data and personal
                   identifiers are removed; a reply that leaked a secret or the prompt is replaced entirely.
Detection runs on a normalised copy of the message: lower case, leetspeak undone, spaced letters joined, and base64
payloads decoded, so "1gn0r3", "i-g-n-o-r-e" and an encoded instruction are seen as what they are.
"""

from __future__ import annotations

import base64
import binascii
import logging
import os
import re
import unicodedata
from dataclasses import dataclass

log = logging.getLogger("hisabdo.ai.guardrails")

VERIFIED_EMAILS = {"hisabdo.app@gmail.com"}
SUPPORT = "hisabdo.app@gmail.com or the Contact page (https://hisabdo.app/contact)"

# ------------------------------------------------------------------------------------ normalisation

LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"})


def normalise(text: str) -> str:
    """Lower-cased, leetspeak undone, s-p-a-c-e-d letters joined, base64 payloads decoded and appended."""
    t = unicodedata.normalize("NFKC", text).lower()
    decoded = []
    for blob in re.findall(r"[A-Za-z0-9+/]{16,}={0,2}", text):
        try:
            d = base64.b64decode(blob + "=" * (-len(blob) % 4), validate=True).decode("utf-8")
            if d.isprintable():
                decoded.append(d.lower())
        except (binascii.Error, UnicodeDecodeError, ValueError):
            pass
    joined = re.sub(r"\b(?:[a-z0-9@$][\s\-_.]{1,3}){3,}[a-z0-9@$]\b",
                    lambda m: re.sub(r"[\s\-_.]", "", m.group(0)), t)
    leet = " ".join(w.translate(LEET) if re.search(r"[a-z]", w) else w for w in joined.split())
    return " ".join([t, joined, leet] + decoded)


# ------------------------------------------------------------------------------------ input rules

RULES: list[tuple[str, list[str]]] = [
    ("self_harm", [
        r"\b(end my life|kill myself|suicide|suicidal|want to die|khud ?kushi|mar jana chahta|jaan de dun)\b",
        r"(خودکشی|مر جانا چاہتا)"]),
    ("prompt_injection", [
        r"\b(ignore|disregard|forget|override|bypass)\b.{0,40}\b(instructions?|rules?|prompts?|guidelines?|polic(y|ies)|"
        r"restrictions?|the above|previous|safety)\b",
        r"\b(previous|prior|above|earlier)\s+instructions\b.{0,30}\b(void|cancel\w*|invalid|null)\b",
        r"<\|im_(start|end)\|>|<\|system\|>|\[/?inst\]|<<\s*/?sys\s*>>|(^|\n)\s*system\s*:|#+\s*(system|instruction)",
        r"\bnew (rule|policy|instructions?)\b.{0,60}\b(loaded|from|you (may|must|can) now)\b",
        r"\b(hidayat|hidayaat|qawaid|rules?)\b.{0,30}\b(bhool|bhul|ignore|nazar andaz|band karo|khatam)",
        r"(ہدایات|ہدایت|قواعد).{0,30}(نظر انداز|بھول|ختم)",
        # spaced or joined letters ("i-g-n-o-r-e y-o-u-r ...") lose their word boundaries
        r"(ignore|disregard|forget)(all|your|the|previous|prior|my){0,3}(instructions|rules|prompts?)"]),
    ("instruction_override", [
        r"\b(developer|dev|god|admin|sudo|jailbreak|unrestricted)\s+mode\b|\bsudo\b",
        r"\b(your|the)\s+(instructions|rules)\s+(have been|are|were)\s+(updated|changed|replaced)\b",
        r"\b(authori[sz]e|allow|permit)\s+you\s+to\s+(bypass|ignore|skip|break)\b",
        r"\b(i am|i'm|main)\b.{0,20}\b(admin|administrator|developer|owner of hisabdo)\b.{0,60}\b(rules?|band|bypass|"
        r"ignore|override|restrictions?)\b",
        r"\byou (may|can) now share\b"]),
    ("jailbreak", [
        r"\b(do anything now|you are (now )?dan|as dan|dan mode)\b",
        r"\b(no|without|zero)\s+(rules|restrictions|filters?|content polic\w*|limits)\b",
        r"\b(koi )?rules? nahi\b",
        r"\b(pretend|imagine|roleplay|role[ -]play|act as)\b.{0,60}\b(unrestricted|unfiltered|no filters?|no rules|"
        r"without (any )?(rules|filters|restrictions))\b",
        r"\bgrand(mother|ma)\b.{0,80}\b(keys?|passwords?|tokens?|secrets?)\b",
        r"\bstory\b.{0,60}\b(hide|evade|launder|fake|hack)\w*\b"]),
    ("prompt_extraction", [
        r"\b(system|hidden|secret|internal|initial)\s+(prompt|message|instructions?|rules)\b",
        r"\b(repeat|print|show|reveal|display|output|summari[sz]e|list|what (are|were))\b.{0,30}\byour\b.{0,25}"
        r"\b(instructions|prompt|rules)\b",
        r"\b(instructions|prompt)\s+you\s+(were|have been)\s+given\b",
        r"\bprint everything above\b|\beverything above this line\b|\bstarting with .you are\b",
        r"system prompt|سسٹم پرامپٹ"]),
    ("secrets", [
        r"\b(api|secret|service|access|private)[\s_-]*keys?\b",
        r"\b(your|the app'?s|the server'?s|database|db|supabase|admin)\s+(password|token|credentials?|secret)\b",
        r"\.env\b|\benvironment (file|variables?)\b|\binternal_service_token\b|\bconnection string\b"]),
    ("privacy", [
        r"\b(all|every|each)\b.{0,30}\b(users?|customers?|people|members)\b.{0,50}\b(phone|numbers?|cnic|address\w*|"
        r"emails?|balances?|transactions|details)\b",
        r"\b(list|export|dump)\b.{0,20}\b(users?|customers?)\b.{0,40}\b(phone|numbers?|cnic|emails?)\b",
        r"\b\d{5}-\d{7}-\d\b",
        r"\b(repeat|say|read|echo)\b.{0,20}\b(back|exactly)\b"]),
    ("unverified_contact", [
        r"\b(personal|private|home|ghar)\b.{0,25}\b(number|phone|whatsapp|email|address|pata)\b",
        r"\b(support|helpline|customer care|office)\s+(phone|number|whatsapp|line)\b",
        r"\b(founder|ceo|owner|usman|khalid)\b.{0,50}\b(number|phone|whatsapp|email|address)\b",
        r"\b(post|publish|add|include|put)\b.{0,40}\b(official|support)\b.{0,25}\b(line|number|email|contact)\b",
        r"\b(backup|alternate|another|other) email\b",
        r"\b(is|confirm)\b[^?]{0,15}\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}"]),
    ("unsafe", [
        r"\b(hide|conceal|under-?report|evade|not declare)\b.{0,40}\b(income|tax|fbr|sales|profit)\b",
        r"\bpay no tax\b|\btax evasion\b|\bevade tax",
        r"\b(fake|forged?|false|bogus|fraudulent)\s+(invoices?|receipts?|bills?|entries|records)\b",
        r"\blaunder\w*\b",
        r"\b(hack|break into|steal|phish)\w*\b.{0,40}\b(account|password|competitor|data)\b",
        r"\b(hisaa?b|khata)\b.{0,30}\b(badal|chhupa|ghalat)\b|\bbina (usay|use|kisi ko) pata chale\b"]),
    ("toxic", [
        r"\b(idiot|stupid|moron|dumb|useless bot|shut up|worthless|trash|bitch|bastard|f+u+c+k\w*)\b",
        r"\b(bewakoof|bekaar|ghatiya|kameena|gadha|ullu|bakwas)\b",
        r"\b(insult\w*|threat\w*|abus\w*|intimidat\w*|blackmail\w*)\b.{0,40}\b(message|text|note|letter|customer|"
        r"supplier|him|her|them)\b",
        r"\b(scare|threaten)\b.{0,30}\b(customer|supplier|him|her|them)\b"]),
    ("out_of_domain_advice", [
        r"\b(stocks?|shares|crypto\w*|bitcoin|forex|gold)\b.{0,40}\b(buy|sell|invest\w*|double|pick)\b|"
        r"\b(buy|sell|invest\w*)\b.{0,40}\b(stocks?|shares|crypto\w*|bitcoin|forex|gold)\b",
        r"\b(medicine|chest pain|symptoms?|disease|dawai|doctor)\b",
        r"\b(legal notice|lawyer|wakeel|divorce|evict\w*|sue|court case)\b"]),
]
COMPILED = [(cat, [re.compile(p, re.I) for p in pats]) for cat, pats in RULES]

REPLIES = {
    "self_harm": ("I'm really sorry you're going through this. You don't have to face it alone. Please talk to someone "
                  "you trust, and if you are in immediate danger in Pakistan, call Rescue 1122. I'm here to help with "
                  "your business records whenever you're ready."),
    "prompt_injection": ("I can't change how I work or follow instructions inside a message. I can help with HisabDo "
                         "and your business records. What would you like to do?"),
    "instruction_override": ("I can't switch modes or turn off my rules, whoever asks. I can help with HisabDo and your "
                             "business records. What would you like to do?"),
    "jailbreak": ("I can't role-play my way around my rules. I can help with HisabDo and your business records. What "
                  "would you like to do?"),
    "prompt_extraction": "I can't share my internal instructions. I can help with HisabDo and your business records.",
    "secrets": "I can't share keys, tokens, passwords or other system credentials.",
    "privacy": ("I can only help with your own account, and I don't repeat or collect personal details such as phone "
                "numbers or CNIC numbers. Please don't share them in chat."),
    "unverified_contact": (f"The only verified way to reach HisabDo is {SUPPORT}. I can't share personal contact "
                           "details or confirm other numbers or addresses."),
    "unsafe": ("I can't help with that. I can help you keep accurate records, track tax-relevant income and expenses, "
               "or prepare a PDF report for your accountant."),
    "toxic": ("I'm here to help with HisabDo and your business records, and I keep things respectful. If a customer "
              "owes you money, I can help you keep a clear record and share a polite PDF statement."),
    "out_of_domain_advice": ("That's outside what I can help with: I don't give medical, legal or investment advice. "
                             "Please ask a qualified professional. I can help with HisabDo and your business records."),
    "off_topic": ("I can help with HisabDo and with bookkeeping for your business, so I can't help with that. Try "
                  f"asking about customers and udhar, expenses, PDF reports or backup, or contact {SUPPORT}."),
    "output_blocked": ("Sorry, I can't share that response. I can help with HisabDo and your business records; "
                       f"for anything else, contact {SUPPORT}."),
}


@dataclass
class GuardVerdict:
    category: str
    reply: str


def check_input(message: str) -> GuardVerdict | None:
    text = normalise(message)
    for category, patterns in COMPILED:
        if any(p.search(text) for p in patterns):
            log.warning("guardrail_input_blocked", extra={"category": category})  # never the message text
            return GuardVerdict(category, REPLIES[category])
    return None


# ------------------------------------------------------------------------------------ domain boundary

DOMAIN = re.compile(
    r"hisab|khata|khaata|udh?aa?r|ledger|expense|kharch|income|aamdani|amdani|customer|grahak|supplier|payment|"
    r"receivable|payable|report|pdf|backup|restore|invoice|bookkeep|accounting|account|balance|budget|cash|profit|"
    r"loss|sale|tax|business|shop|dukaan|dukan|money|paise|paisa|rupee|pkr|financ|record|entry|entries|transaction|"
    r"statement|credit|debt|loan|qarz|salary|rent|bill|price|cost|app\b|sync|offline|internet|language|currency|"
    r"support|password|staff|stock purchase|inventory|supplier|vendor|bank|reminder|back ?up|data|phone|device|"
    r"spen[dt]|earn|owe|owed|paid|pay\b|bought|sold|month|week|"
    r"delete|sign ?in|login|android|iphone|ios|"
    r"حساب|کھات|ادھار|خرچ|آمدنی|کاروبار|دکان|پیس|رپورٹ|گاہک|بیک اپ|انٹرنیٹ",
    re.I)


QUESTION = re.compile(r"\?|؟|^\s*(who|what|when|where|why|which|how|kya|kaun|kon|kab|kahan|kaise)", re.I)
TRANSACTION_VERB = re.compile(r"(diye|diya|liye|liya|mile|mila|kharid\w*|bech\w*|paid|received|spent|bought|sold|"
                              r"got|gave|wasool|bhara|bhari|di|li)", re.I)


def check_off_topic_question(message: str, history: str = "") -> GuardVerdict | None:
    """Before the router: a question with no business word and no transaction verb is off topic. (The router reads any
    number as an amount, so "Who won the 1992 world cup?" would otherwise start an expense entry.)"""
    if QUESTION.search(message) and not TRANSACTION_VERB.search(message):
        return check_domain(message, history)
    return None


def check_domain(message: str, history: str = "") -> GuardVerdict | None:
    """General-route boundary: nothing about HisabDo, bookkeeping or business money -> boundary reply. `history` = the
    recent turns, so a follow-up ("What about the batch version?") keeps the topic of the conversation."""
    if DOMAIN.search(message) or DOMAIN.search(history):
        return None
    log.info("guardrail_off_topic")
    return GuardVerdict("off_topic", REPLIES["off_topic"])


# ------------------------------------------------------------------------------------ output validation

SECRET_SHAPES = re.compile(r"\b(sk-[A-Za-z0-9]{16,}|AIza[0-9A-Za-z_-]{30,}|gsk_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,})")
ENV_NAMES = re.compile(r"\b(INTERNAL_SERVICE_TOKEN|[A-Z]+_API_KEY|SUPABASE_[A-Z_]*KEY|DATABASE_URL)\b")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?:\+92[\s-]?|0)3\d{2}[\s-]?\d{7}\b|\+\d{1,3}[\s-]?\(?\d{2,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,4}\b")
CNIC = re.compile(r"\b\d{5}-\d{7}-\d\b")
REDACTED = "[removed]"


def _secret_values() -> list[str]:
    return [v for k, v in os.environ.items()
            if re.search(r"TOKEN|KEY|SECRET|PASSWORD", k) and isinstance(v, str) and len(v) >= 8]


def _prompt_fingerprints() -> list[str]:
    from .prompts import GROUNDING_RULES, SYSTEM_PROMPT
    lines = [l.strip(" -") for l in (SYSTEM_PROMPT + "\n" + GROUNDING_RULES).splitlines()]
    return [l[:60].lower() for l in lines if len(l) > 40]


def check_output(reply: str) -> tuple[str, list[str]]:
    """(safe reply, findings). Secrets or prompt text -> whole reply replaced; contacts and identifiers -> removed."""
    findings = []
    low = reply.lower()
    if any(v in reply for v in _secret_values()) or SECRET_SHAPES.search(reply) or ENV_NAMES.search(reply):
        findings.append("secret")
    if any(f in low for f in _prompt_fingerprints()):
        findings.append("prompt_text")
    if findings:
        log.warning("guardrail_output_blocked", extra={"findings": findings})
        return REPLIES["output_blocked"], findings
    out = EMAIL.sub(lambda m: m.group(0) if m.group(0).lower() in VERIFIED_EMAILS else REDACTED, reply)
    out = CNIC.sub(REDACTED, PHONE.sub(REDACTED, out))
    if out != reply:
        findings.append("contact_or_identifier_removed")
        log.warning("guardrail_output_redacted")
    return out, findings
