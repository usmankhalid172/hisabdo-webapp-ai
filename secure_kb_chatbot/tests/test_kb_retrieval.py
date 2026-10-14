"""Semantic search, relevance threshold, source attribution, safe fallback, KB versioning."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import create_app
from chatbot.kb import KBError, chunk_entries, load_kb
from chatbot.prompts import RULES
from chatbot.retrieval import KBRetriever, NoteIndex, build_index
from chatbot.vector_store import VectorStore
from conftest import OTHER_TENANT, OWNER, TODAY, FakeLLM, ok
from kb_helpers import FIXTURES, ConceptEmbedder, shared_words

ROOT = Path(__file__).parent.parent


@pytest.fixture
def embedder():
    return ConceptEmbedder()


@pytest.fixture
def store(repo, embedder):
    s = VectorStore(repo)
    version, _, _ = build_index(s, embedder, FIXTURES / "kb_v1")
    s.activate(version)
    return s


@pytest.fixture
def retriever(store, embedder):
    return KBRetriever(store, embedder, threshold=0.60, top_k=4)


def kb_client(repo, embedder, llm):
    return TestClient(create_app(repo, llm_factory=lambda: llm, today=TODAY, embedder_factory=lambda: embedder))


# --- knowledge base files: verified only, validated ---------------------------------------------


def test_only_verified_entries_are_indexed():
    version, entries = load_kb(FIXTURES / "kb_v1")
    chunks = chunk_entries(version, entries)
    assert version == "1.0.0" and len(entries) == 4
    assert {c.entry_id for c in chunks} == {"KB-001", "KB-002", "KB-101"}  # KB-003 is a draft


def test_docs_are_split_by_section_and_keep_their_source():
    _, entries = load_kb(FIXTURES / "kb_v1")
    doc = [c for c in chunk_entries("1.0.0", entries) if c.entry_id == "KB-101"]
    assert [c.section for c in doc] == ["Credit sales", "Payments"]
    assert all(c.source == "fixture guide s.7" and c.title == "Customer balances" for c in doc)


def test_shipped_kb_is_valid_and_all_draft():
    """The starter KB must load, and must not be quotable until a person verifies entries."""
    version, entries = load_kb(ROOT / "kb" / "v1")
    assert entries and chunk_entries(version, entries) == []


@pytest.mark.parametrize(
    "change, message",
    [
        ({"id": "KB-001"}, "duplicate id"),
        ({"id": "FAQ-9"}, "must look like KB-001"),
        ({"verified_by": ""}, "need verified_by"),
        ({"verified_on": "last week"}, "verified_on as YYYY-MM-DD"),
        ({"status": "approved"}, "status must be"),
        ({"answer": ""}, "empty title/question or body/answer"),
    ],
)
def test_invalid_kb_is_rejected(tmp_path, change, message):
    entry = {"id": "KB-009", "question": "Q?", "answer": "A.", "status": "verified",
             "verified_by": "Someone", "verified_on": "2026-10-13"}
    first = {**entry, "id": "KB-001"}
    (tmp_path / "manifest.json").write_text('{"kb_version": "9.9.9"}')
    (tmp_path / "faqs.json").write_text(json.dumps([first, {**entry, **change}]))
    with pytest.raises(KBError, match=message):
        load_kb(tmp_path)


# --- semantic search replaces token matching -------------------------------------------------------


def test_finds_the_answer_when_no_words_match(retriever):
    question = "kharcha kaise likhun?"  # Roman Urdu for "how do I write down an expense?"
    result = retriever.retrieve(question)
    assert result.status == "ok" and result.sources[0].id == "KB-001"
    passage = result.sources[0].passages[0][1]
    assert shared_words(question, passage) == set()  # keyword matching would have scored this 0


def test_most_relevant_source_ranks_first(retriever):
    assert retriever.retrieve("What is the price of the plan?").sources[0].id == "KB-002"
    assert retriever.retrieve("udhaar balance").sources[0].id == "KB-101"


# --- relevance threshold -----------------------------------------------------------------------------


def test_off_topic_question_retrieves_nothing(retriever):
    result = retriever.retrieve("Give me a biryani recipe")
    assert result.status == "no_match" and result.sources == ()
    assert result.best_score is not None and result.best_score < result.threshold


def test_threshold_controls_what_is_returned(store, embedder):
    question = "expense payment report"  # only loosely related to any single entry
    loose = KBRetriever(store, embedder, threshold=0.10).retrieve(question)
    strict = KBRetriever(store, embedder, threshold=0.99).retrieve(question)
    assert loose.status == "ok" and strict.status == "no_match"
    assert strict.best_score == loose.best_score  # same search, different cut-off


def test_every_returned_source_meets_the_threshold(retriever):
    for q in ("kharcha", "price", "udhaar payment", "export excel"):
        assert all(s.score >= retriever.threshold for s in retriever.retrieve(q).sources)


# --- safe fallback ------------------------------------------------------------------------------------


def test_embedding_outage_is_reported_not_raised(retriever, embedder):
    embedder.fail = True
    assert retriever.retrieve("kharcha kaise likhun?").status == "unavailable"


def test_no_active_version_is_empty(repo, embedder):
    assert KBRetriever(VectorStore(repo), embedder).retrieve("kharcha").status == "empty"


def test_index_built_with_another_model_is_not_used(store, embedder):
    embedder.model = "a-different-model"
    assert KBRetriever(store, embedder).retrieve("kharcha").status == "unavailable"


@pytest.mark.parametrize(
    "question, status",
    [("Give me a biryani recipe", "no_match"), ("kharcha kaise likhun?", "ok")],
)
def test_model_is_told_the_retrieval_status(repo, store, embedder, question, status):
    llm = FakeLLM()
    kb_client(repo, embedder, llm).post("/api/chat", json={"message": question}, headers=OWNER)
    context = llm.calls[0]["system"][1]["text"]
    assert f'<knowledge_base status="{status}"' in context
    if status == "no_match":
        assert "<kb_source" not in context  # nothing irrelevant is shown to the model


def test_prompt_contains_the_fallback_rule():
    assert 'status "no_match" or "empty"' in RULES and "contacting HisabDo support" in RULES
    assert "ONLY from <knowledge_base>" in RULES


def test_chat_still_works_when_embeddings_are_down(repo, store, embedder):
    embedder.fail = True
    llm = FakeLLM(ok("Product information is temporarily unavailable. [U-001]", ["U-001"], grounding="insufficient_data"))
    r = kb_client(repo, embedder, llm).post("/api/chat", json={"message": "kharcha kaise likhun?"}, headers=OWNER)
    assert r.status_code == 200 and r.json()["knowledge_base"]["status"] == "unavailable"
    assert '<knowledge_base status="unavailable"/>' in llm.calls[0]["system"][1]["text"]


def test_without_embeddings_configured_status_is_unavailable(client, llm):
    """Default test client has no embedder at all (no API key)."""
    r = client.post("/api/chat", json={"message": "How do I record an expense?"}, headers=OWNER).json()
    assert r["knowledge_base"]["status"] == "unavailable" and r["sources"] == []


# --- source attribution -------------------------------------------------------------------------------


def test_answer_reports_the_sources_it_cited(repo, store, embedder):
    llm = FakeLLM(ok("Open Expenses, enter the amount and category, then save [KB-001].", ["KB-001"]))
    r = kb_client(repo, embedder, llm).post("/api/chat", json={"message": "kharcha kaise likhun?"}, headers=OWNER).json()
    assert r["grounding"] == "grounded" and r["citations"] == ["KB-001"]
    assert r["sources"] == [{"id": "KB-001", "title": "How do I record an expense?", "source": "fixture guide s.4",
                             "kb_version": "1.0.0", "relevance": r["sources"][0]["relevance"]}]
    assert r["sources"][0]["relevance"] >= 0.60
    assert r["knowledge_base"] == {"status": "ok", "version": "1.0.0", "best_score": r["knowledge_base"]["best_score"],
                                   "threshold": 0.6}
    context = llm.calls[0]["system"][1]["text"]
    assert '<kb_source id="KB-001" title="How do I record an expense?" source="fixture guide s.4"' in context


def test_citing_a_kb_entry_that_was_not_retrieved_is_stripped(repo, store, embedder):
    llm = FakeLLM(ok("Prices are on the pricing page [KB-002].", ["KB-002"]))
    r = kb_client(repo, embedder, llm).post("/api/chat", json={"message": "kharcha kaise likhun?"}, headers=OWNER).json()
    assert r["citations"] == [] and r["sources"] == [] and "[KB-002]" not in r["answer"]
    assert r["grounding"] == "partial" and "KB-002" in r["warnings"][0]


def test_only_cited_sources_are_attributed(repo, store, embedder):
    llm = FakeLLM(ok("A credit sale adds to the balance [KB-101].", ["KB-101"]))
    r = kb_client(repo, embedder, llm).post("/api/chat", json={"message": "udhaar payment"}, headers=OWNER).json()
    assert [s["id"] for s in r["sources"]] == ["KB-101"]


# --- versioning ----------------------------------------------------------------------------------------


def test_new_version_is_not_live_until_activated_and_can_be_rolled_back(store, embedder):
    retriever = KBRetriever(store, embedder)
    assert retriever.retrieve("which reports").status == "no_match"  # 1.0.0 has no reports entry

    version, indexed, drafts = build_index(store, embedder, FIXTURES / "kb_v2")
    assert (version, indexed, drafts) == ("1.1.0", 5, 1)
    assert store.active_version() == "1.0.0" and retriever.retrieve("which reports").status == "no_match"

    store.activate("1.1.0")
    result = retriever.retrieve("which reports")
    assert result.sources[0].id == "KB-004" and result.sources[0].kb_version == "1.1.0"

    store.activate("1.0.0")  # rollback: no re-indexing needed
    assert retriever.retrieve("which reports").status == "no_match"
    assert store.versions() == {"1.0.0": 4, "1.1.0": 5}


def test_cannot_activate_a_version_that_was_never_indexed(store):
    with pytest.raises(ValueError, match="has not been indexed"):
        store.activate("7.0.0")


def test_reindexing_a_version_replaces_it(store, embedder):
    build_index(store, embedder, FIXTURES / "kb_v1")
    assert store.versions() == {"1.0.0": 4}


# --- notes: semantic search instead of keyword overlap ----------------------------------------------------


def test_note_found_by_meaning_without_shared_words(repo, embedder):
    question = "udhaar ki had kis ne barhane ko kaha?"  # "who asked to raise the credit limit?"
    llm = FakeLLM()
    VectorStore(repo)
    kb_client(repo, embedder, llm).post("/api/chat", json={"message": question}, headers=OWNER)
    context = llm.calls[0]["system"][1]["text"]
    assert 'id="N-002"' in context  # "Bilal asked to raise Qureshi Mart's credit limit..."
    assert 'id="N-003"' not in context  # unrelated note stays out
    note = next(n for n in repo.list("notes", "B-001") if n.id == "N-002")
    assert shared_words(question, note.content) == set()


def test_notes_are_embedded_once_and_again_only_when_changed(repo, embedder):
    index = NoteIndex(VectorStore(repo), embedder, threshold=0.5)
    notes = repo.list("notes", "B-001")
    q = embedder.embed_query("udhaar")
    index.rank("B-001", notes, q)
    index.rank("B-001", notes, q)
    assert len(embedder.document_calls) == 1 and len(embedder.document_calls[0]) == len(notes)

    repo.update("notes", "B-001", "N-001", {"content": "Ahmed will make the payment on Friday"})
    index.rank("B-001", repo.list("notes", "B-001"), q)
    assert embedder.document_calls[-1] == ["Ahmed will make the payment on Friday"]


def test_deleted_note_vector_is_removed(repo, embedder):
    store = VectorStore(repo)
    index = NoteIndex(store, embedder, threshold=0.5)
    q = embedder.embed_query("udhaar")
    index.rank("B-001", repo.list("notes", "B-001"), q)
    repo.delete("notes", "B-001", "N-002")
    ranked = index.rank("B-001", repo.list("notes", "B-001"), q)
    assert "N-002" not in store.note_vectors("B-001", embedder.model) and all(n.id != "N-002" for n in ranked)


def test_note_vectors_never_cross_businesses(repo, embedder):
    store = VectorStore(repo)
    index = NoteIndex(store, embedder, threshold=0.0)
    q = embedder.embed_query("hedge")
    index.rank("B-001", repo.list("notes", "B-001"), q)
    index.rank("B-002", repo.list("notes", "B-002"), q)
    assert set(store.note_vectors("B-002", embedder.model)) == {"N-101"}
    assert "N-101" not in store.note_vectors("B-001", embedder.model)
    with pytest.raises(ValueError, match="another business"):
        index.rank("B-001", repo.list("notes", "B-002"), q)


def test_other_tenant_context_has_only_their_notes(repo, embedder):
    llm = FakeLLM()
    kb_client(repo, embedder, llm).post("/api/chat", json={"message": "udhaar credit limit"}, headers=OTHER_TENANT)
    context = llm.calls[0]["system"][1]["text"]
    assert "N-002" not in context and "Qureshi" not in context


def test_keyword_matching_is_the_fallback_when_embeddings_fail(repo, embedder):
    embedder.fail = True
    llm = FakeLLM()
    kb_client(repo, embedder, llm).post("/api/chat", json={"message": "notes about credit limit"}, headers=OWNER)
    assert 'id="N-002"' in llm.calls[0]["system"][1]["text"]  # found by the shared words "credit limit"
