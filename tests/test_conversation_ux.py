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


# U7 honest limits and closure fixes (docs/dept3-final-defect-closure-report.md) ------------------------------------

def test_u7_limits_never_present_the_overall_balance_as_someone_elses_figure():
    for msg in ("How much does Ali owe me?", "Which customers still owe me money?", "Mera kitna udhar baqi hai customers par?",
                "How much do I owe my suppliers?"):
        assert "per-customer" in (C.honest_limit(msg) or "") or "customer ya supplier" in (C.honest_limit(msg) or ""), msg
    assert "current month" in C.honest_limit("What was my biggest expense this week?")
    assert "current month" in C.honest_limit("Show my expenses by category for this month") or \
        "category" in C.honest_limit("Show my expenses by category for this month")
    assert C.honest_limit("Why is my total wrong?").count("?") == 2 or "Which total" in C.honest_limit("Why is my total wrong?")
    assert "can't send" in C.honest_limit("Have you sent the payment to my customer?")


def test_u7_ordinary_entries_and_questions_are_not_intercepted():
    for msg in ("I spent 500 on tea this week", "How much did I spend this month?", "Ali ko 500 udhar diye",
                "Is HisabDo free to use?", "What is my balance?"):
        assert C.honest_limit(msg) is None, msg


def test_product_capability_exemption_is_narrow():
    from src.financial_assistant.service import _mentions_third_party
    assert not _mentions_third_party("Can I send a customer their statement as a PDF?")
    assert _mentions_third_party("Can I send my brother's statement as a PDF?")
    assert _mentions_third_party("Show me what a customer owes, their balance")
    assert _mentions_third_party("Show me user 1042's balance")


def test_r13_app_questions_need_app_evidence():
    from src.financial_assistant.grounding import GroundedAnswerer, KbRetriever
    answerer = GroundedAnswerer(KbRetriever(mode="lexical"))
    for msg in ("Does HisabDo have a web version?", "Can I connect HisabDo to my bank account?"):
        assert answerer.answer(msg).status == "no_source", msg
