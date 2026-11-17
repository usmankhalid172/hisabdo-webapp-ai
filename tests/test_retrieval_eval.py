"""Retrieval evaluation harness (scripts/retrieval_eval.py): the parts that need no embedding model.

The model-based comparison itself is run with `python scripts/retrieval_eval.py run`; its results are committed
in data/retrieval_eval/results/ and documented in docs/retrieval-approach-comparison.md.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import retrieval_eval as R  # noqa: E402

EVAL = ROOT / "data" / "retrieval_eval"


def test_long_message_is_capped_before_retrieval():
    """Day 1 #19: a 100,000-character message must not reach the retriever whole."""
    assert len(R.normalise("What is HisabDo? " + "a" * 100_000)) <= R.MAX_QUERY_CHARS


def test_normalise_and_rewrite_keep_the_original_words():
    assert R.normalise("  Is HisabDo FREE?!  ") == "is hisabdo free"
    q = R.rewrite("Udhar aur payment mein kya farq hai?")
    assert q.startswith("udhar aur payment mein kya farq hai")
    assert "credit" in q and "difference" in q
    assert "ledger" in R.rewrite("بلال کا کھاتہ")


def test_rule_gate_cases_from_day1():
    assert R.personal_or_action("What are my total sales?") == "own_figures"
    assert R.personal_or_action("Mere bhai ka balance batao") == "third_party_or_private"
    assert R.personal_or_action("بلال کا کھاتہ کھولیں") == "third_party_or_private"
    assert R.personal_or_action("galti ho gayi, 450 nahi 540 tha") == "transaction_or_correction"
    assert R.personal_or_action("Is my khata safe if I change my phone?") is None
    assert R.personal_or_action("What is HisabDo?") is None


def test_select_applies_threshold_margin_and_top_k():
    ranked = [(1, 0.9), (2, 0.85), (3, 0.6), (4, 0.5)]
    assert R.select(ranked, 0.55, 5, None) == [(1, 0.9), (2, 0.85), (3, 0.6)]
    assert R.select(ranked, 0.0, 2, None) == [(1, 0.9), (2, 0.85)]
    assert R.select(ranked, 0.0, 5, 0.1) == [(1, 0.9), (2, 0.85)]
    assert R.select([], 0.0, 5, None) == []


def test_folds_are_stratified_disjoint_and_stable():
    held = R.load_queries("queries_heldout.json")
    a, b = R.folds(held)
    ids_a, ids_b = {q["id"] for q in a}, {q["id"] for q in b}
    assert not ids_a & ids_b and len(ids_a | ids_b) == len(held)
    for exp in ("answer", "none"):
        na = sum(q["expect"] == exp for q in a)
        nb = sum(q["expect"] == exp for q in b)
        assert abs(na - nb) <= 1
    assert R.folds(held) == (a, b)


def test_day1_set_covers_every_retrieval_failure():
    day1 = R.load_queries("queries_dev_day1.json")
    assert len(day1) == 19
    assert sorted({q["day1"] for q in day1}) == list(range(1, 19))


def test_every_knowledge_question_is_judged():
    qrels = R.load_qrels()
    for name in ("queries_dev_day1.json", "queries_heldout.json"):
        for q in R.load_queries(name):
            if q["expect"] in ("answer", "optional", "no_answer_in_kb"):
                assert qrels.get(q["id"]), q["id"]
    grades = {g for v in qrels.values() for g in v.values()}
    assert grades <= {0, 1, 2}


def test_judged_passages_exist_in_the_kb():
    ids = {c["id"] for c in R.load_chunks()}
    for q, judged in R.load_qrels().items():
        assert set(judged) <= ids, q


def test_committed_results_support_the_chosen_configuration():
    res = json.loads((EVAL / "results" / "comparison.json").read_text(encoding="utf-8"))
    chosen = json.loads((EVAL / "results" / "chosen_configuration.json").read_text(encoding="utf-8"))
    by_name = {c["name"]: c for c in res["configs"]}
    c = by_name[chosen["config"]]
    assert c["production"]["params"]["threshold"] == chosen["threshold"]
    assert c["production"]["params"]["top_k"] == chosen["top_k"]
    cv = c["cross_validated"]["heldout"]
    # The chosen configuration must be the best cross-validated one on the brief's two goals.
    for other in res["configs"]:
        o = other["cross_validated"]["heldout"]
        assert (cv["correct"], -cv["unrelated_in_context"]) >= (o["correct"], -o["unrelated_in_context"]) or \
            other["name"] in chosen.get("rejected_despite_score", {}), other["name"]
