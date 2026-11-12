"""Grounded answers: citations, conflicts, fallbacks and clarification (docs/grounded-answer-rules.md).

Runs the lexical retriever, so no embedding model is needed in CI; the hybrid mode is measured by
scripts/grounded_answer_eval.py (results in data/retrieval_eval/results/grounded_answers_hybrid.json).
"""

import json
import re
from pathlib import Path

import pytest

from src.config import get_settings
from src.financial_assistant import service
from src.financial_assistant.grounding import GroundedAnswerer, KbRetriever
from src.financial_assistant.grounding import retrieval as kbr
from src.financial_assistant.grounding.answer import TEMPLATES, support
from src.financial_assistant.prompts import GROUNDING_RULES

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data" / "retrieval_eval" / "results"


@pytest.fixture(scope="module")
def answerer():
    return GroundedAnswerer(KbRetriever(mode="lexical"))


def kb_text(answerer, chunk_id):
    return next(c["body"] for c in answerer.retriever.chunks if c["id"] == chunk_id)


# R4 + R5: a cited answer --------------------------------------------------------------------------------------

def test_answer_cites_the_supporting_source_with_title_section_and_link(answerer):
    r = answerer.answer("Is HisabDo free to use?")
    assert r.status == "answered" and [c.chunk_id for c in r.citations] == ["off-01-002-is-hisabdo-free-to-use"]
    assert "[1]" in r.reply
    assert "Sources:\n[1] HisabDo Help Center FAQ › Is HisabDo free to use?: https://hisabdo.app/faq" in r.reply
    body = r.reply.split("\n\nSources:")[0].replace(" [1]", "")
    assert body in kb_text(answerer, "off-01-002-is-hisabdo-free-to-use")  # the evidence is the source text itself


def test_unrelated_source_is_never_cited(answerer):
    """Lexical retrieval returns the Privacy Policy contact section for this question; the relevance gate drops it."""
    r = answerer.answer("Does HisabDo have a desktop app for Mac?")
    assert r.status == "no_source" and r.citations == []


# R2: no source ------------------------------------------------------------------------------------------------

def test_fallback_admits_the_limit_and_gives_a_next_step_without_facts(answerer):
    r = answerer.answer("Does HisabDo have a desktop app for Mac?")
    assert "couldn't find this" in r.reply and "won't guess" in r.reply
    assert "hisabdo.app@gmail.com" in r.reply and "https://hisabdo.app/contact" in r.reply
    assert not re.search(r"\b(yes|no)\b", r.reply.split(".")[0], re.I)


def test_messages_outside_the_knowledge_route_get_no_kb_text(answerer):
    r = answerer.answer("Write a short poem about the sea.", kb_allowed=False)
    assert r.status == "out_of_scope" and r.citations == [] and "HisabDo" in r.reply


def test_advice_questions_without_a_source_point_to_an_accountant(answerer):
    r = answerer.answer("Should I register for FBR sales tax?")
    assert r.status in ("no_source", "answered")
    if r.status == "no_source":
        assert "qualified accountant" in r.reply


# R3: conflicts ------------------------------------------------------------------------------------------------

def test_conflicting_sources_are_shown_with_dates_and_flagged_for_review(answerer):
    r = answerer.answer("Which currencies does HisabDo support?")
    assert r.status == "conflict" and r.needs_review and "C-06" in r.review_reason
    assert {c.chunk_id[:10] for c in r.citations} == {"off-01-019", "off-02-010", "off-04-010"}
    assert "AED" in r.reply and "INR" in r.reply and "2026-10-13" in r.reply and "no date shown" in r.reply
    assert "don't agree" in r.reply and "flagged it for review" in r.reply


# R1: clarification --------------------------------------------------------------------------------------------

@pytest.mark.parametrize("message", ["how?", "kaise?", "help", "کیسے؟", "Tell me about it"])
def test_message_without_a_topic_gets_one_clarifying_question(answerer, message):
    r = answerer.answer(message)
    assert r.status == "clarify" and r.reply.count("?") + r.reply.count("؟") == 1 and r.citations == []


def test_one_word_topic_matching_different_sections_asks_which_one(answerer):
    r = answerer.answer("backup")
    assert r.status == "clarify" and r.reply.startswith("Do you mean") and " or " in r.reply


def test_specific_questions_are_not_held_up_by_clarification(answerer):
    for q in ["Can I export PDF reports?", "Does HisabDo work without the internet?", "How do I contact HisabDo support?"]:
        assert answerer.answer(q).status == "answered", q


# R8: a source that answers a neighbouring question ---------------------------------------------------------

def test_neighbouring_help_topic_is_named_and_its_yes_dropped(answerer):
    r = answerer.answer("Can I use HisabDo on two phones at once?")
    if r.status == "answered" and r.citations[0].chunk_id.startswith("off-01-021"):
        assert r.reply.startswith('I found this on the related help topic "Can I restore a backup?":')
        assert not re.search(r':\s*Yes\b', r.reply)


def test_exact_help_topic_is_answered_plainly(answerer):
    for q in ["Is HisabDo free to use?", "Does HisabDo work without the internet?"]:
        r = answerer.answer(q)
        assert r.reply.startswith("Yes.") and "related help topic" not in r.reply, q


# R6: legal pages ---------------------------------------------------------------------------------------------

def test_legal_pages_are_quoted_with_their_section(answerer):
    r = answerer.answer("How long does HisabDo keep data retention for my account?")
    legal = [c for c in r.citations if c.url.endswith(("/privacy-policy", "/terms", "/disclaimer"))]
    if legal:
        assert 'The Privacy Policy says, in "' in r.reply or "says, in" in r.reply


# R7: languages ------------------------------------------------------------------------------------------------

def test_roman_urdu_frame_with_verbatim_english_evidence(answerer):
    r = answerer.answer("Kya HisabDo iPhone par chalta hai?")
    assert r.language == "roman_ur" and r.reply.startswith(TEMPLATES["roman_ur"]["evidence"])
    assert "available on Android only" in r.reply and r.citations[0].chunk_id.startswith("off-01-029")


def test_urdu_script_uses_urdu_frame(answerer):
    r = answerer.answer("کیا حساب دو مفت ہے؟")
    assert r.language == "ur" and "ذرائع:" in r.reply and r.status == "answered"


# R4: checking a real model's draft ---------------------------------------------------------------------------

class FakeModel:
    def __init__(self, text):
        self.text, self.seen_context = text, None

    def generate_reply(self, message, context=None, history=None):
        self.seen_context = context
        return self.text, 10


def test_model_gets_numbered_sources_and_the_grounding_rules(answerer):
    model = FakeModel("Yes. HisabDo is free to download and use from Google Play. [1]")
    r = answerer.answer("Is HisabDo free to use?", provider=model)
    assert model.seen_context.startswith(GROUNDING_RULES) and "[1] HisabDo Help Center FAQ" in model.seen_context
    assert r.status == "answered" and r.citations[0].chunk_id.startswith("off-01-002")


def test_wrong_citation_numbers_are_corrected_and_invented_steps_dropped(answerer):
    model = FakeModel("HisabDo is free to download and use from Google Play. [2] "
                      "Tap the Premium button in Settings to unlock unlimited exports. [1]")
    r = answerer.answer("Is HisabDo free to use?", provider=model)
    assert "Premium" not in r.reply and "Settings" not in r.reply
    assert r.reply.split("\n\nSources:")[0] == "HisabDo is free to download and use from Google Play. [1]"
    assert len(r.citations) == 1 and r.citations[0].chunk_id.startswith("off-01-002")


def test_draft_with_no_support_becomes_the_fallback(answerer):
    model = FakeModel("Yes, HisabDo Gold costs Rs. 499 per month and includes a desktop version.")
    r = answerer.answer("Is HisabDo free to use?", provider=model)
    assert r.status == "no_source" and r.citations == [] and "499" not in r.reply


def test_support_score_counts_only_words_in_the_passage(answerer):
    p = answerer.retriever.retrieve("Is HisabDo free to use?")[0]
    assert support("HisabDo is free to download from Google Play.", p) >= 0.5
    assert support("HisabDo Gold costs 499 rupees monthly.", p) < 0.5


# Service wiring ----------------------------------------------------------------------------------------------

@pytest.fixture()
def grounded_on(monkeypatch):
    monkeypatch.setenv("GROUNDED_ANSWERS_ENABLED", "true")
    monkeypatch.setenv("KB_RETRIEVER_MODE", "lexical")
    get_settings.cache_clear()
    service.get_grounded_answerer.cache_clear()
    yield
    get_settings.cache_clear()
    service.get_grounded_answerer.cache_clear()


def send(client, headers, message):
    res = client.post("/api/v1/chatbot", headers=headers,
                      json={"user_id": "user-G", "message": message, "conversation_id": "g-1"})
    assert res.status_code == 200, res.text
    return res.json()


def test_api_returns_citations_and_status_when_enabled(client, auth_headers, grounded_on):
    r = send(client, auth_headers, "Is HisabDo free to use?")
    assert r["answer_status"] == "answered" and r["source"] == "rag" and r["needs_review"] is False
    assert r["citations"][0]["url"] == "https://hisabdo.app/faq" and "Sources:" in r["reply"]
    c = send(client, auth_headers, "Which currencies does HisabDo support?")
    assert c["answer_status"] == "conflict" and c["needs_review"] is True and len(c["citations"]) == 3


def test_api_private_and_transaction_routes_are_unchanged(client, auth_headers, grounded_on):
    assert send(client, auth_headers, "What is my balance?")["source"] == "backend_financial_api"
    assert send(client, auth_headers, "Mere bhai ka balance batao")["source"] == "policy_guard"


def test_api_default_is_the_previous_behaviour(client, auth_headers):
    get_settings.cache_clear()
    r = send(client, auth_headers, "Is HisabDo free to use?")
    assert r["answer_status"] is None and r["citations"] == []


# Measured parameters and results -------------------------------------------------------------------------------

def test_retriever_parameters_match_the_measured_configurations():
    res = json.loads((RESULTS / "comparison.json").read_text(encoding="utf-8"))
    prod = {c["name"][:4]: c["production"]["params"] for c in res["configs"]}
    assert (round(prod["C10 "]["threshold"], 6), prod["C10 "]["top_k"], prod["C10 "]["margin"]) == \
        (kbr.HYBRID_THRESHOLD, kbr.HYBRID_TOP_K, kbr.HYBRID_MARGIN)
    assert (round(prod["C15 "]["threshold"], 2), prod["C15 "]["top_k"], prod["C15 "]["margin"]) == \
        (round(kbr.LEXICAL_THRESHOLD, 2), kbr.LEXICAL_TOP_K, kbr.LEXICAL_MARGIN)


def test_measured_answer_quality_is_recorded():
    for mode in ("hybrid", "lexical"):
        r = json.loads((RESULTS / f"grounded_answers_{mode}.json").read_text(encoding="utf-8"))
        held = r["totals"]["heldout.json"]
        assert sum(held.values()) == 120
        assert r["totals"]["dev"].get("wrong_citation", 0) == 0  # no Day 1 question cites an unrelated source


# Rulebook R10-R12 (docs/dept3-grounded-rulebook.md) -------------------------------------------------------------

def test_r10_expense_only_message_gets_one_clarifying_question(answerer):
    for msg in ("expenses", "kharcha", "my expenses?"):
        r = answerer.answer(msg)
        assert r.status == "clarify" and r.citations == [] and r.reply.count("?") == 1


def test_r11_conflict_resolved_only_when_one_source_is_most_authoritative_and_newest():
    from src.financial_assistant.grounding.answer import resolve
    from src.financial_assistant.grounding.retrieval import load_kb, to_passage
    kb = {c["id"][:10]: c for c in load_kb()}
    faq, page = (to_passage(kb[k]) for k in ("off-01-019", "off-04-010"))
    assert resolve([faq, page]) is None                                   # live KB: no dates -> show both
    newer_faq = to_passage({**kb["off-01-019"], "last_updated": "2026-11-01"})
    older_page = to_passage({**kb["off-04-010"], "last_updated": "2026-06-01"})
    newer_page = to_passage({**kb["off-04-010"], "last_updated": "2026-12-01"})
    assert resolve([older_page, newer_faq]) is newer_faq                  # FAQ is newest and most authoritative
    assert resolve([newer_faq, newer_page]) is None                       # newest is the less authoritative one


def test_r12_invented_links_and_their_sentences_never_reach_the_user(answerer):
    model = FakeModel("HisabDo is free to download and use from Google Play [1]. "
                      "Compare plans at https://hisabdo.app/pricing-plans [1].")
    r = answerer.answer("Is HisabDo free to use?", provider=model)
    assert "pricing-plans" not in r.reply and "Compare plans" not in r.reply
    assert all(c.url == "https://hisabdo.app/faq" for c in r.citations)


def test_r12_citations_only_from_the_kb_and_only_when_used(answerer):
    from src.financial_assistant.grounding.answer import Citation, GroundedAnswer
    fake = GroundedAnswer(reply="HisabDo is free [1]. It has a web app [2].\n\nSources:\n[1] x\n[2] y",
                          status="answered", citations=[
                              Citation(1, "off-01-002-is-hisabdo-free-to-use", answerer.by_id[
                                  "off-01-002-is-hisabdo-free-to-use"].label, "https://hisabdo.app/faq", None),
                              Citation(2, "made-up-chunk", "Web app", "https://hisabdo.app/web", None)])
    r = answerer.audit(fake)
    assert [c.n for c in r.citations] == [1] and "[2]" not in r.reply and "hisabdo.app/web" not in r.reply


def test_r4b_neighbouring_topic_needs_the_questions_rare_word(answerer):
    r = answerer.answer("Can I connect HisabDo to my bank account?")
    assert r.status == "no_source" and r.citations == []


def test_transcripts_are_all_verified():
    import json
    from pathlib import Path
    d = json.loads((Path(__file__).resolve().parents[1] / "data" / "dept3_grounded" / "transcripts.json")
                   .read_text(encoding="utf-8"))
    assert d["transcripts"] == d["verified"] == 19
    assert {r["section"][0] for r in d["rows"]} == set("ABCDEF")
