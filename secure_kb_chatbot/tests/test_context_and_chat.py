"""AI team deliverable: context model, context-aware prompting, grounded answers."""

from chatbot import validate
from chatbot.prompts import RULES
from conftest import OWNER, TODAY, ok

# --- business context model -------------------------------------------------------------


def test_how_much_does_ahmed_owe_context(builder):
    b = builder.build("U-001", "How much does Ahmed owe?", TODAY)
    assert b.focus_customer_ids == ["C-001"]
    # Precomputed balance: R-001 40,000 (overdue) + R-002 45,000 left = 85,000.
    assert 'outstanding_balance="85000.00" overdue_balance="40000.00"' in b.text
    assert set(b.included["receivables"]) == {"R-001", "R-002", "R-003"}
    assert 'id="R-001"' in b.text and 'state="overdue"' in b.text
    assert "N-001" in b.included["notes"]  # "promised to clear INV-1041 by 10 October"
    assert b.included["payables"] == []  # customer debt question: vendors not loaded


def test_user_and_business_context_always_present(builder):
    b = builder.build("U-002", "hello", TODAY)
    assert '<current_user id="U-002" name="Omar Siddiqui" role="Sales Manager"' in b.text
    assert 'name="Al-Madina Traders"' in b.text and 'currency="PKR"' in b.text
    assert '<policy name="credit_hold">' in b.text
    assert 'outstanding_total="220000.00"' in b.text  # receivables summary
    assert 'outstanding_total="198000.00"' in b.text  # payables summary


def test_who_owes_us_loads_all_open_receivables(builder):
    b = builder.build("U-001", "Who owes us money?", TODAY)
    assert set(b.included["receivables"]) == {"R-001", "R-002", "R-004", "R-006"}  # paid ones excluded
    assert b.included["receivables"][0] in {"R-001", "R-006"}  # overdue first
    assert b.included["payables"] == []


def test_what_do_we_owe_loads_payables(builder):
    b = builder.build("U-001", "How much do we owe our suppliers?", TODAY)
    assert set(b.included["payables"]) == {"P-001", "P-002"}
    assert b.included["receivables"] == []


def test_vendor_by_name(builder):
    b = builder.build("U-001", "What's left to pay Punjab Edible Oils?", TODAY)
    assert b.included["payables"] == ["P-001"] and 'outstanding="150000.00"' in b.text


def test_customer_context_by_company_and_id(builder):
    assert builder.build("U-001", "Summarize Qureshi Mart", TODAY).focus_customer_ids == ["C-002"]
    assert builder.build("U-001", "status of C-003?", TODAY).focus_customer_ids == ["C-003"]


def test_task_context_overdue_and_mine(builder):
    assert set(builder.build("U-001", "Which tasks are overdue?", TODAY).included["tasks"]) == {"T-001", "T-003"}
    mine = builder.build("U-002", "what are my tasks this week?", TODAY).included["tasks"]
    assert set(mine) == {"T-001", "T-002"}


def test_notes_context_is_escaped_and_marked_untrusted(builder):
    b = builder.build("U-001", "Sana Iqbal notes", TODAY)
    assert "N-004" in b.included["notes"] and '<notes untrusted_content="true">' in b.text


def test_follow_up_uses_conversation_focus(builder):
    b = builder.build("U-001", "and what tasks are open for them?", TODAY, focus_customer_ids=["C-001"])
    assert b.focus_customer_ids == ["C-001"] and "T-001" in b.included["tasks"]


def test_same_first_name_loads_every_match(client, builder):
    client.post("/api/customers", json={"name": "Ahmed Raza", "company": "Raza Traders"}, headers=OWNER)
    b = builder.build("U-001", "How much does Ahmed owe?", TODAY)
    assert len(b.focus_customer_ids) == 2  # model is told to ask which Ahmed
    assert "more than one customer" in RULES


# --- context-aware prompting -------------------------------------------------------------


def test_context_is_injected_into_system_prompt(client, llm):
    llm.results = [ok("Ahmed Hassan owes PKR 85,000.00 [C-001]; PKR 40,000.00 is overdue [R-001].", ["C-001", "R-001"])]
    r = client.post("/api/chat", json={"message": "How much does Ahmed owe?"}, headers=OWNER)
    assert r.status_code == 200
    call = llm.calls[0]
    rules, context = call["system"]
    assert rules["text"] == RULES and rules["cache_control"] == {"type": "ephemeral"}
    assert context["text"].startswith('<business_context as_of="2026-10-07">')
    assert 'outstanding_balance="85000.00"' in context["text"]
    assert call["messages"] == [{"role": "user", "content": "How much does Ahmed owe?"}]

    body = r.json()
    assert body["grounding"] == "grounded" and body["warnings"] == []
    assert body["citations"] == ["C-001", "R-001"]


def test_follow_up_turn_sends_history_and_fresh_context(client, llm):
    llm.results = [ok("PKR 85,000.00 [C-001].", ["C-001"]), ok("One task [T-001].", ["T-001"])]
    sid = client.post("/api/chat", json={"message": "How much does Ahmed owe?"}, headers=OWNER).json()["conversation_id"]
    client.patch("/api/receivables/R-001", json={"amount_paid": 40000}, headers=OWNER)  # Ahmed pays INV-1041
    client.post("/api/chat", json={"message": "Any tasks for him?", "conversation_id": sid}, headers=OWNER)

    second = llm.calls[1]
    assert [m["role"] for m in second["messages"]] == ["user", "assistant", "user"]
    assert second["messages"][1]["content"] == "PKR 85,000.00 [C-001]."
    ctx = second["system"][1]["text"]
    assert 'outstanding_balance="45000.00"' in ctx  # fresh from DB, not the old snapshot
    assert "T-001" in ctx  # "him" resolved via conversation focus


def test_failed_turn_is_not_added_to_history(client, llm):
    from chatbot import LLMResult

    llm.results = [LLMResult(stop_reason="refusal", data=None), ok("ok [U-001].", ["U-001"])]
    sid = client.post("/api/chat", json={"message": "first"}, headers=OWNER).json()["conversation_id"]
    client.post("/api/chat", json={"message": "second", "conversation_id": sid}, headers=OWNER)
    assert llm.calls[1]["messages"] == [{"role": "user", "content": "second"}]


# --- grounding checks on the AI response --------------------------------------------------


def _ctx(builder, q="How much does Ahmed owe?"):
    return builder.build("U-001", q, TODAY)


def test_grounded_answer_passes(builder):
    b = _ctx(builder)
    raw = {"answer": "Ahmed owes Rs 85,000 [C-001], incl. PKR 40,000.00 overdue [R-001].",
           "citations": ["C-001", "R-001"], "grounding": "grounded", "missing_information": []}
    r = validate(raw, b.source_ids, b.text)
    assert r.grounding == "grounded" and r.warnings == []


def test_invented_amount_is_flagged(builder):
    b = _ctx(builder)
    raw = {"answer": "Ahmed owes Rs 92,500 [C-001].", "citations": ["C-001"],
           "grounding": "grounded", "missing_information": []}
    r = validate(raw, b.source_ids, b.text)
    assert r.grounding == "partial" and "Rs 92,500" in r.warnings[0]


def test_south_asian_grouping_and_shorthand(builder):
    b = _ctx(builder, "Who owes us money?")
    raw = {"answer": "Bilal owes Rs 1,20,000 [R-004]; Ahmed about PKR 85k [C-001].", "citations": ["R-004", "C-001"],
           "grounding": "grounded", "missing_information": []}
    assert validate(raw, b.source_ids, b.text).warnings == []


def test_citation_to_record_not_loaded_is_removed(builder):
    b = _ctx(builder)
    raw = {"answer": "Also see the vendor bill [P-001].", "citations": ["P-001"],
           "grounding": "grounded", "missing_information": []}
    r = validate(raw, b.source_ids, b.text)
    assert "[P-001]" not in r.answer and r.citations == [] and r.grounding == "partial"


def test_grounded_without_citations_is_downgraded(builder):
    b = _ctx(builder)
    raw = {"answer": "Ahmed owes a bit.", "citations": [], "grounding": "grounded", "missing_information": []}
    assert validate(raw, b.source_ids, b.text).grounding == "partial"
