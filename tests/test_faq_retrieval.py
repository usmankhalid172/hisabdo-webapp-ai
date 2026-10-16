"""RAG-xx: reworked FAQ retrieval - aliases, multilingual, threshold, source attribution, safe fallback."""
import json
import re
from pathlib import Path

import numpy as np
import pytest

from src.financial_assistant.faq_rag import RELEVANCE_THRESHOLD, FaqRetriever, normalise
from src.financial_assistant.service import handle_chat
from src.schemas import ChatbotRequest

ROOT = Path(__file__).resolve().parents[1]
R = FaqRetriever()


@pytest.mark.parametrize("question, doc", [
    ("Explain what this app is for", "faq-001"),                         # paraphrase, no shared keyword
    ("Can I download my spending as a spreadsheet?", "faq-005"),
    ("HisabDo kya hai?", "faq-001"), ("حساب دو کیا ہے؟", "faq-001"),        # brand-only question
    ("Revenue kya hota hai?", "finance_002"),                            # Roman Urdu function words ignored
    ("Profit aur cash flow mein kya farq hai?", "faq-006"),
    ("Kya chatbot Urdu samajhta hai?", "faq-007"),                       # previously missing source
])
def test_RAG_01_paraphrased_and_multilingual_questions_find_the_right_document(question, doc):
    assert R.retrieve(question)[0]["id"] == doc


@pytest.mark.parametrize("question", ["How much does HisabDo cost per month?", "What is the HisabDo support phone number?",
                                      "HisabDo ki monthly fees kitni hai?", "Does HisabDo work offline?",
                                      "Who won the cricket match yesterday?"])
def test_RAG_02_no_verified_source_returns_nothing(question):
    assert R.retrieve(question) == []       # the brand word alone no longer drags in faq-001


def test_RAG_03_threshold_is_applied():
    strict = FaqRetriever(threshold=0.99)
    assert strict.retrieve("Why should I label my business costs?") == []
    assert RELEVANCE_THRESHOLD == R.threshold


def test_RAG_04_response_carries_source_attribution():
    resp = handle_chat(ChatbotRequest(user_id="u", message="How do I export my expenses?", conversation_id="rag-4"))
    assert resp.source == "rag" and resp.sources[0].id == "faq-005" and resp.sources[0].score > 0
    assert "[Source: How do I export my expenses?]" in resp.reply      # the label reaches the model (mock echoes it)


def test_RAG_05_product_question_without_source_gets_safe_fallback_not_an_llm_guess(monkeypatch):
    from src.financial_assistant import service
    monkeypatch.setattr(service, "get_llm_provider", lambda: (_ for _ in ()).throw(AssertionError("LLM called")))
    resp = handle_chat(ChatbotRequest(user_id="u", message="How much does HisabDo cost per month?", conversation_id="rag-5"))
    assert resp.source == "kb_fallback" and resp.sources == [] and "won't guess" in resp.reply
    ru = handle_chat(ChatbotRequest(user_id="u", message="HisabDo ka discount code kya hai?", conversation_id="rag-5b"))
    assert ru.source == "kb_fallback" and "andaza nahi" in ru.reply


def test_RAG_06_optional_semantic_layer_is_blended_in():
    class FakeEmbedder:
        """Puts every text containing 'zebra' at the same point: a 'meaning' the lexical views can't see."""
        def embed(self, texts):
            m = np.array([[1.0, 0.0] if "zebra" in t.lower() or "export" in t.lower() else [0.0, 1.0] for t in texts])
            return m / np.linalg.norm(m, axis=1, keepdims=True)
    semantic = FaqRetriever(embedder=FakeEmbedder())
    assert semantic.retrieve("zebra")[0]["id"] == "faq-005"
    assert R.retrieve("zebra") == []


def test_RAG_07_new_kb_entry_quote_exists_in_its_source_file():
    docs = json.loads((ROOT / "data" / "faq_docs.json").read_text(encoding="utf-8"))
    for d in docs:
        if "source" in d:
            assert d["source"]["quote"] in (ROOT / d["source"]["file"]).read_text(encoding="utf-8")


def test_RAG_08_aliases_are_not_copies_of_evaluation_questions():
    norm = lambda s: re.sub(r"[^\w]+", " ", s.lower()).strip()  # noqa: E731
    docs = json.loads((ROOT / "data" / "faq_docs.json").read_text(encoding="utf-8"))
    aliases = {norm(a) for d in docs for a in d.get("aliases", [])}
    for name in ("dept3_eval_set.json", "dept3_heldout_set.json", "dept3_heldout_round2.json"):
        cases = json.loads((ROOT / "tests" / "evaluation" / "dept3" / name).read_text(encoding="utf-8"))["cases"]
        assert not [c["id"] for c in cases if norm(c["q"]) in aliases], name


def test_RAG_09_normalise_keeps_topic_and_drops_function_words():
    assert "kya" not in normalise("Revenue kya hota hai?").split()
    assert "revenue" in normalise("Revenue kya hota hai?").split()
