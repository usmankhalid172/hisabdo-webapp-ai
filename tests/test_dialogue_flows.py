"""FLOW-xx: multi-turn slot filling, confirmation, corrections, routing (dialogue manager, no HTTP)."""
from datetime import date, datetime, timedelta, timezone

import pytest

from src.financial_assistant.dialogue import ConversationState, DialogueManager, FlowStatus, Intent, Route
from src.financial_assistant.dialogue.account_data import AccountRef, FakeAccountData

USER = "11111111-1111-1111-1111-111111111111"
OTHER = "22222222-2222-2222-2222-222222222222"
TODAY = date(2026, 10, 14)


def manager(currency="PKR", accounts=None, account_data=None):
    data = account_data or FakeAccountData(accounts if accounts is not None else
                                           {USER: [AccountRef(id="a1", name="Personal")]})
    return DialogueManager(account_data=data, default_currency=lambda u: currency, today=lambda: TODAY)


def chat(m, *messages, state=None, user=USER):
    state = state or ConversationState()
    outs = [m.handle(user, msg, state) for msg in messages]
    return outs, state


# ------------------------------------------------------------------ expense / income
def test_FLOW_01_complete_expense_in_one_message_then_confirm():
    (o1, o2), state = chat(manager(), "Aaj 500 ka petrol dala", "haan")
    assert o1.status == FlowStatus.AWAITING_CONFIRMATION and "PKR 500" in o1.reply and "Transport" in o1.reply
    assert o1.action is None                                  # nothing final before the user says yes
    assert o2.status == FlowStatus.COMPLETED and o2.action.type == "create_expense"
    assert o2.action.payload == {"amount": "500.00", "currency": "PKR", "category": "Transport",
                                 "date": "2026-10-14"}
    assert state.active_intent is None and len(state.recent_actions) == 1


def test_FLOW_02_missing_category_is_asked_then_filled():
    (o1, o2, o3), _ = chat(manager(), "Ali ko 500 diye", "sabzi aur doodh", "ji")
    assert o1.status == FlowStatus.COLLECTING and o1.missing_slots == ["category"] and "kis cheez" in o1.reply
    assert "Utilities" in o1.reply                                   # options are the team's categories
    assert o2.status == FlowStatus.AWAITING_CONFIRMATION
    assert o3.action.payload["category"] == "Groceries" and o3.action.payload["counterparty"] == "Ali"


def test_FLOW_02b_user_can_type_their_own_category():
    (_, o2, o3), _ = chat(manager(), "Ali ko 500 diye", "dukaan ka saman", "ji")
    assert o3.action.payload["category"] == "Dukaan Ka Saman"


def test_FLOW_03_missing_amount_is_asked_and_a_bad_answer_is_asked_again():
    (o1, o2, o3), state = chat(manager(), "Kal kharcha kiya rent ka", "kaafi zyada tha", "1200")
    assert o1.missing_slots == ["amount"] and o1.reply == "Kitne paise the?"
    assert o2.status == FlowStatus.COLLECTING and "wazeh amount" in o2.reply      # never guesses an amount
    assert o3.status == FlowStatus.AWAITING_CONFIRMATION and "PKR 1,200, Housing, 13 Oct 2026" in o3.reply


def test_FLOW_04_unclear_direction_is_asked():
    (o1, o2, o3), _ = chat(manager(), "500", "kharcha", "bijli ka bill")
    assert o1.missing_slots == ["direction"]
    assert o2.missing_slots == ["category"]
    assert o3.status == FlowStatus.AWAITING_CONFIRMATION and "Utilities" in o3.reply


def test_FLOW_05_income_flow_in_english():
    (o1, o2, o3), _ = chat(manager(), "I received 2000", "from sales", "yes")
    assert "What was this income from" in o1.reply
    assert o2.reply.startswith("Please confirm this income")
    assert o3.action.type == "create_income" and o3.action.payload["category"] == "Sales"


def test_FLOW_06_currency_is_asked_when_unknown_never_assumed():
    (o1, o2), _ = chat(manager(currency=None), "Aaj 500 ka petrol dala", "PKR")
    assert o1.missing_slots == ["currency"]
    assert o2.status == FlowStatus.AWAITING_CONFIRMATION and "PKR 500" in o2.reply


def test_FLOW_07_explicit_currency_wins_over_profile():
    (o1,), _ = chat(manager(currency="PKR"), "paid $20 for petrol")
    assert "USD 20" in o1.reply


def test_FLOW_08_change_during_confirmation():
    (_, o2, o3), _ = chat(manager(), "Aaj 500 ka petrol dala", "nahi 700 tha", "haan")
    assert o2.status == FlowStatus.AWAITING_CONFIRMATION and "PKR 700" in o2.reply
    assert o3.action.payload["amount"] == "700.00"


def test_FLOW_09_no_cancels_and_nothing_is_saved():
    (_, o2), state = chat(manager(), "Aaj 500 ka petrol dala", "nahi")
    assert o2.status == FlowStatus.CANCELLED and o2.action is None and state.recent_actions == []


def test_FLOW_10_cancel_while_collecting():
    (_, o2), state = chat(manager(), "Ali ko 500 diye", "rehne do")
    assert o2.status == FlowStatus.CANCELLED and state.active_intent is None


def test_FLOW_11_unclear_reply_to_confirmation_asks_again():
    (_, o2), state = chat(manager(), "Aaj 500 ka petrol dala", "hmm")
    assert o2.status == FlowStatus.AWAITING_CONFIRMATION and "haan" in o2.reply
    assert state.awaiting == "confirmation"


def test_FLOW_12_new_entry_replaces_unfinished_one():
    (_, o2), state = chat(manager(), "Ali ko 500 diye", "Bilal ko 300 diye")
    assert "Pichli adhoori entry" in o2.reply and state.slots.amount == 300 and state.slots.counterparty == "Bilal"


def test_FLOW_13_side_question_keeps_the_unfinished_entry():
    (_, o2, o3), state = chat(manager(), "Aaj 500 ka petrol dala", "HisabDo kya hai?", "haan")
    assert o2.route == Route.KNOWLEDGE and o2.reply is None and "adhoori entry" in o2.pending_reminder
    assert o3.action.type == "create_expense"


def test_FLOW_14_too_many_follow_ups_resets():
    m = manager()
    outs, state = chat(m, "Ali ko 500 diye", *["hmm"] * 8)
    assert any(o.status == FlowStatus.CANCELLED for o in outs) and state.active_intent is None


def test_FLOW_15_unfinished_flow_expires_after_30_minutes():
    m = manager()
    _, state = chat(m, "Ali ko 500 diye")
    state.updated_at = datetime.now(timezone.utc) - timedelta(minutes=31)
    out = m.handle(USER, "haan", state)
    assert out.intent == Intent.CONFIRM and out.status == FlowStatus.NONE   # old entry forgotten, not saved


def test_FLOW_16_urdu_script_gets_roman_urdu_replies():
    (o1,), _ = chat(manager(), "آج 500 کا پٹرول خریدا")
    assert "Yeh kharcha confirm karein" in o1.reply


# ------------------------------------------------------------------ corrections and categories
def test_FLOW_17_correct_last_entry_amount():
    (_, _, o3, o4), state = chat(manager(), "Aaj 500 ka petrol dala", "haan", "last wali entry 600 kar do", "haan")
    first_id = state.recent_actions[-1].action_id
    assert "PKR 500" in o3.reply and "PKR 600" in o3.reply
    assert o4.action.type == "update_transaction"
    assert o4.action.payload == {"target_action_id": first_id, "changes": {"amount": "600.00"}}


def test_FLOW_18_change_category_of_last_entry():
    (_, _, o3, o4), _ = chat(manager(), "Aaj 500 ka petrol dala", "haan", "pichli entry ki category Housing kar do", "haan")
    assert o4.action.payload["changes"] == {"category": "Housing"}


def test_FLOW_19_delete_last_entry():
    (_, _, o3, o4), state = chat(manager(), "Aaj 500 ka petrol dala", "haan", "delete the last entry", "yes")
    assert o4.action.type == "delete_transaction" and state.recent_actions == []


def test_FLOW_20_correction_without_details_asks_what_to_change():
    (_, _, o3, o4, o5), _ = chat(manager(), "Aaj 500 ka petrol dala", "haan", "pichli entry galat hai", "750", "haan")
    assert o3.missing_slots == ["changes"]
    assert o5.action.payload["changes"] == {"amount": "750.00"}


def test_FLOW_21_correction_with_nothing_to_correct_explains():
    (o1,), _ = chat(manager(), "last wali entry 600 kar do")
    assert o1.route == Route.TRANSACTION and "app mein" in o1.reply and o1.action is None


def test_FLOW_22_category_question_gets_a_suggestion():
    (o1,), _ = chat(manager(), "petrol kis category mein aayega?")
    assert o1.intent == Intent.CATEGORIZE and "Transport" in o1.reply


def test_FLOW_22b_how_to_categorize_is_a_product_question():
    (o1,), _ = chat(manager(), "How do I categorize an expense?")
    assert o1.route == Route.KNOWLEDGE and o1.reply is None


# ------------------------------------------------------------------ private route
def test_FLOW_23_report_asks_period_then_uses_the_data_api():
    data = FakeAccountData({USER: [AccountRef(id="a1", name="Personal")]})
    (o1, o2), _ = chat(manager(account_data=data), "report dikhao", "pichle mahine")
    assert o1.route == Route.ACCOUNT_DATA and o1.missing_slots == ["period"]
    assert o2.status == FlowStatus.COMPLETED and "September 2026" in o2.reply and "PKR 150,000" in o2.reply
    assert ("summary", USER) in data.calls


def test_FLOW_24_several_accounts_asks_which_one():
    data = FakeAccountData({USER: [AccountRef(id="a1", name="Personal"), AccountRef(id="a2", name="Corner Shop")]})
    (o1, o2), _ = chat(manager(account_data=data), "is mahine ki report dikhao", "2")
    assert o1.missing_slots == ["account"] and "1) Personal 2) Corner Shop" in o1.reply
    assert o2.reply.startswith("Corner Shop (October 2026)")


def test_FLOW_25_balance_question():
    (o1,), _ = chat(manager(), "mera balance kitna hai?")
    assert o1.intent == Intent.ACCOUNT_QUERY and o1.route == Route.ACCOUNT_DATA and "PKR 153,499.20" in o1.reply


def test_FLOW_26_not_connected_data_says_so_and_invents_nothing():
    from src.financial_assistant.dialogue.account_data import NotConnectedAccountData
    (o1,), _ = chat(manager(account_data=NotConnectedAccountData()), "mera balance kitna hai?")
    assert "nahi dekh sakta" in o1.reply and not any(ch.isdigit() for ch in o1.reply)


def test_FLOW_27_data_api_error_is_a_safe_message():
    (o1,), _ = chat(manager(account_data=FakeAccountData(fail=True)), "What is my balance?")
    assert "couldn't load" in o1.reply


def test_FLOW_28_only_the_callers_own_user_id_is_sent_to_the_data_api():
    data = FakeAccountData({USER: [AccountRef(id="a1", name="Personal")], OTHER: []})
    chat(manager(account_data=data), "mera balance kitna hai?", user=OTHER)
    assert all(uid == OTHER for _, uid in data.calls)


def test_FLOW_29_quick_private_question_during_an_entry_keeps_the_entry():
    (_, o2, o3), _ = chat(manager(), "Aaj 500 ka petrol dala", "mera balance kitna hai?", "haan")
    assert o2.route == Route.ACCOUNT_DATA and "adhoori entry" in o2.reply
    assert o3.action.type == "create_expense"


@pytest.mark.parametrize("text, route", [("HisabDo kya hai?", Route.KNOWLEDGE), ("hello", Route.GENERAL),
                                         ("Give me tips to grow sales", Route.GENERAL)])
def test_FLOW_30_faq_and_general_go_to_the_ai_model(text, route):
    (o1,), _ = chat(manager(), text)
    assert o1.route == route and o1.reply is None


def test_FLOW_31_yes_with_nothing_pending():
    (o1,), _ = chat(manager(), "haan")
    assert o1.status == FlowStatus.NONE and "koi cheez" in o1.reply
