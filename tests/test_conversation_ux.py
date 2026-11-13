"""Conversation UX rules U4-U6 (docs/dept3-conversation-ux-rulebook.md) and the verified transcript runs."""

import json
from pathlib import Path

from src.financial_assistant import conversation as C

D = Path(__file__).resolve().parents[1] / "data" / "dept3_conversation"


def test_u4_account_level_problems_escalate_to_human_support():
    for msg in ("I can't log in to my account", "please delete my account", "Someone else is logged into my account",
                "my records are gone after the update", "mera data gayab ho gaya", "I was charged twice"):
        reply = C.escalation(msg)
        assert reply and "hisabdo.app@gmail.com" in reply and ("password" in reply or "OTP" in reply), msg


def test_u4_ordinary_entries_and_questions_do_not_escalate():
    for msg in ("Delete the expense I just added", "How do I back up my data?", "I spent 500 on tea",
                "What happens to my data if I uninstall the app?", "Can I create an account?"):
        assert C.escalation(msg) is None, msg


def test_u5_second_fallback_uses_the_short_form():
    full = ("I couldn't find this in HisabDo's official help pages, so I won't guess. You can ask HisabDo support at "
            "hisabdo.app@gmail.com or through the Contact page (https://hisabdo.app/contact); they aim to reply "
            "within 48 hours.")
    assert C.dedupe(full, "fallback", [], "Can I connect my bank?") == full
    short = C.dedupe(full, "fallback", [full], "Can two staff use one account?")
    assert short == C.REPEAT["en"]["fallback"] and len(short) < len(full)


def test_u6_answer_to_the_expense_question_is_mapped():
    q = C.TEMPLATES["en"]["clarify_expense"]
    assert C.follow_up("how expense tracking works", q) == "What does the HisabDo expense tracker do?"
    assert C.follow_up("show my totals", q) == "How much did I spend this month?"
    assert C.follow_up("how expense tracking works", "Something else?") is None


def test_transcripts_and_adversarial_log_are_verified():
    t = json.loads((D / "transcripts.json").read_text(encoding="utf-8"))
    a = json.loads((D / "adversarial_log.json").read_text(encoding="utf-8"))
    assert len(t["journeys"]) == t["journeys_verified"] == 8 and t["turns"] == 22
    assert len(a["attacks"]) == a["attacks_held"] == 18
