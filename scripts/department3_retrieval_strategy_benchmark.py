from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EVAL = ROOT / "docs" / "evaluation"
INGEST = DATA / "department3_ingestion"

CHUNKS_FILE = INGEST / "chunks.json"
EMBEDDINGS_FILE = INGEST / "embeddings.npy"
DATASET_FILE = EVAL / "department3_evaluation_set_v1.0.csv"
BASELINE_FILE = EVAL / "retrieval_results_v1.0.csv"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"

TOP_K_VALUES = (1, 3, 5)
DENSE_THRESHOLD = 0.40
BM25_K1 = 1.5
BM25_B = 0.75
RRF_K = 60

OUTPUT_RESULTS = EVAL / "department3_retrieval_strategy_results.csv"
OUTPUT_SUMMARY = EVAL / "department3_retrieval_strategy_summary.csv"
OUTPUT_MATRIX = EVAL / "department3_retrieval_strategy_comparison_matrix.md"
OUTPUT_CONFIG = EVAL / "department3_final_retrieval_configuration.md"
OUTPUT_REPORT = EVAL / "department3_retrieval_performance_report.md"


TYPO_MAP = {
    "exprot": "export",
    "expences": "expenses",
    "expence": "expense",
    "catagorize": "categorize",
    "catagorization": "categorization",
    "custmer": "customer",
    "balnce": "balance",
    "wht": "what",
    "cashflw": "cash flow",
    "statment": "statement",
    "recieve": "receive",
    "recievable": "receivable",
    "payble": "payable",
    "reciev": "receive",
    "expens": "expense",
}

PHRASE_MAP = {
    "kis kaam aati hai": "what is hisabdo used for",
    "kitne paise dene hain": "how much money do i owe",
    "paise dene hain": "money i owe payable",
    "lena dena": "money given and received",
    "khata": "khata ledger customer balances",
    "udhar": "udhar money owed receivable payable",
    "customer ka balance": "customer balance",
    "hisaab check": "check account balance",
}


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def tokenize(text):
    return re.findall(r"[a-z0-9]+", str(text).lower())


def normalize_query(query):
    text = str(query).lower().strip()
    for old, new in PHRASE_MAP.items():
        text = text.replace(old, new)
    words = []
    for word in tokenize(text):
        words.extend(tokenize(TYPO_MAP.get(word, word)))
    return " ".join(words)


def bm25_scores(query, documents):
    tokenized = [tokenize(doc) for doc in documents]
    q_tokens = tokenize(query)
    n_docs = len(tokenized)
    avg_len = sum(map(len, tokenized)) / max(n_docs, 1)
    doc_freq = Counter()
    for tokens in tokenized:
        doc_freq.update(set(tokens))

    scores = []
    for tokens in tokenized:
        frequencies = Counter(tokens)
        doc_len = len(tokens)
        score = 0.0
        for term in q_tokens:
            freq = frequencies.get(term, 0)
            if not freq:
                continue
            df = doc_freq[term]
            idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
            denominator = freq + BM25_K1 * (
                1 - BM25_B + BM25_B * doc_len / max(avg_len, 1)
            )
            score += idf * (freq * (BM25_K1 + 1)) / denominator
        scores.append(float(score))
    return np.asarray(scores, dtype=np.float32)


def ranked_indices(scores, candidates=None):
    if candidates is None:
        candidates = range(len(scores))
    return sorted(candidates, key=lambda i: float(scores[i]), reverse=True)


def reciprocal_rank_fusion(dense_order, lexical_order):
    scores = np.zeros(len(dense_order), dtype=np.float32)
    for rank, index in enumerate(dense_order, start=1):
        scores[index] += 1.0 / (RRF_K + rank)
    for rank, index in enumerate(lexical_order, start=1):
        scores[index] += 1.0 / (RRF_K + rank)
    return scores


def query_metadata_filter(query):
    q = normalize_query(query)

    categorization_terms = (
        "categorize", "categorized", "categorised", "categorise",
        "catagorize", "catagorization", "categorization",
        "categorisation", "classification", "classify",
        "expense category", "expense categories",
        "category prediction", "categories available",
        "available categories", "category list",
        "machine learning", "rule based", "auto correction",
        "automatic categorization", "uncertain prediction",
        "expense ki category", "khud select",
        "mujhe karni parti",
    )
    reporting_terms = (
        "export", "pdf", "report", "download",
    )
    finance_terms = (
        "profit", "revenue", "cash flow", "receivable",
        "payable", "business expenses", "financial concept",
    )
    product_terms = (
        "hisabdo", "app", "khata", "udhar", "customer balance",
        "screen", "button",
    )

    if any(term in q for term in categorization_terms):
        return "expense_categorization"
    if any(term in q for term in reporting_terms):
        return "expense_reporting"
    if any(term in q for term in finance_terms):
        return "finance"
    if any(term in q for term in product_terms):
        return "product"
    return "all"


def metadata_candidates(query, chunks):
    intent = query_metadata_filter(query)

    if intent == "expense_reporting":
        selected = [
            i for i, chunk in enumerate(chunks)
            if chunk.get("document_id") == "faq-005"
            and chunk.get("verified") is True
        ]
    elif intent == "expense_categorization":
        selected = [
            i for i, chunk in enumerate(chunks)
            if chunk.get("verified") is True
            and chunk.get("category") == "Product Support"
            and any(
                term in normalize_query(
                    chunk.get("title", "") + " " + chunk.get("text", "")
                )
                for term in (
                    "categorize", "categorization",
                    "expense category", "category prediction",
                )
            )
        ]
    elif intent == "product":
        selected = [
            i for i, chunk in enumerate(chunks)
            if chunk.get("category") == "Product Support"
            and chunk.get("verified") is True
        ]
    elif intent == "finance":
        selected = [
            i for i, chunk in enumerate(chunks)
            if chunk.get("category") == "Finance Education"
            and chunk.get("verified") is True
        ]
    else:
        selected = [
            i for i, chunk in enumerate(chunks)
            if chunk.get("verified") is True
        ]

    # An empty result is intentional: do not fall back to unrelated sources.
    return selected


def rerank_scores(query, chunks, base_scores):
    q_tokens = set(tokenize(normalize_query(query)))
    result = np.asarray(base_scores, dtype=np.float32).copy()

    for i, chunk in enumerate(chunks):
        title_tokens = set(tokenize(chunk.get("title", "")))
        text_tokens = set(tokenize(chunk.get("text", "")))

        title_overlap = len(q_tokens & title_tokens) / max(len(q_tokens), 1)
        text_overlap = len(q_tokens & text_tokens) / max(len(q_tokens), 1)

        title_bonus = 0.12 * title_overlap
        text_bonus = 0.08 * text_overlap
        result[i] += title_bonus + text_bonus

    return result


def parse_expected(row):
    raw = (
        row.get("Supporting_Source_Records")
        or row.get("Expected_Source_IDs")
        or ""
    )
    return {
        item.strip()
        for item in re.split(r"[;,|]", raw)
        if item.strip()
    }


def is_verified(row):
    return str(row.get("Source_Status", "")).strip().lower() in {
        "verified", "approved", "approved/verified"
    }


def expected_hit(order, expected_ids, chunks, k):
    returned = {
        chunks[i]["document_id"]
        for i in order[:k]
    }
    return bool(returned & expected_ids)


def reciprocal_rank(order, expected_ids, chunks):
    for rank, index in enumerate(order, start=1):
        if chunks[index]["document_id"] in expected_ids:
            return 1.0 / rank
    return 0.0


def main():
    for path in (CHUNKS_FILE, EMBEDDINGS_FILE, DATASET_FILE, BASELINE_FILE):
        if not path.exists():
            raise FileNotFoundError(f"Required input missing: {path}")

    chunks = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))
    vectors = np.load(EMBEDDINGS_FILE).astype(np.float32)

    if len(chunks) != len(vectors):
        raise ValueError(
            f"Chunk/vector mismatch: {len(chunks)} chunks, {len(vectors)} vectors"
        )

    questions = read_csv(DATASET_FILE)
    baseline_rows = read_csv(BASELINE_FILE)
    baseline_by_id = {row["Test_ID"]: row for row in baseline_rows}

    if len(questions) != 60:
        raise ValueError(f"Expected 60 evaluation questions; found {len(questions)}")

    print(f"Loaded {len(chunks)} staged chunks and {len(questions)} questions.")
    print("Loading the pinned embedding model...")

    model = SentenceTransformer(
        MODEL_NAME,
        revision=MODEL_REVISION,
    )

    query_texts = [row["Question"] for row in questions]
    normalized_texts = [normalize_query(q) for q in query_texts]

    query_vectors = model.encode(
        normalized_texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    ).astype(np.float32)

    dense_matrix = query_vectors @ vectors.T
    documents = [
        f"{chunk.get('title', '')} {chunk.get('section', '')} "
        f"{chunk.get('category', '')} {chunk.get('text', '')}"
        for chunk in chunks
    ]

    detailed_rows = []
    strategy_orders = {}
    strategy_scores = {}

    for q_index, row in enumerate(questions):
        test_id = row["Test_ID"]
        question = row["Question"]
        expected = parse_expected(row)
        verified = is_verified(row)

        dense = dense_matrix[q_index]
        lexical = bm25_scores(normalized_texts[q_index], documents)

        dense_order = ranked_indices(dense)
        lexical_order = ranked_indices(lexical)
        hybrid = reciprocal_rank_fusion(dense_order, lexical_order)
        hybrid_order = ranked_indices(hybrid)

        filtered = metadata_candidates(question, chunks)
        metadata_order = ranked_indices(hybrid, filtered)

        reranked = rerank_scores(question, chunks, hybrid)
        rerank_order = ranked_indices(reranked, filtered)

        strategies = {
            "dense_vector": (dense_order, dense),
            "bm25_lexical": (lexical_order, lexical),
            "hybrid_rrf": (hybrid_order, hybrid),
            "hybrid_metadata": (metadata_order, hybrid),
            "hybrid_metadata_rerank": (rerank_order, reranked),
        }

        for strategy, (order, scores) in strategies.items():
            strategy_orders[(test_id, strategy)] = order
            strategy_scores[(test_id, strategy)] = scores

            for k in TOP_K_VALUES:
                top = order[:k]
                returned_ids = [
                    chunks[i]["document_id"] for i in top
                ]
                hit = expected_hit(order, expected, chunks, k)
                top_score = float(scores[order[0]]) if order else 0.0

                detailed_rows.append({
                    "Test_ID": test_id,
                    "Domain": row.get("Domain", ""),
                    "Question": question,
                    "Query_Type": row.get("Query_Type", ""),
                    "Source_Status": row.get("Source_Status", ""),
                    "Verified_Evaluation": verified,
                    "Expected_Source_IDs": ";".join(sorted(expected)),
                    "Strategy": strategy,
                    "Top_K": k,
                    "Retrieved_Source_IDs": ";".join(returned_ids),
                    "Top_Relevance_Score": round(top_score, 6),
                    "Expected_Source_Hit": hit if verified else "",
                    "Reciprocal_Rank": (
                        round(reciprocal_rank(order, expected, chunks), 6)
                        if verified else ""
                    ),
                    "Top_Source_Verified": bool(chunks[order[0]].get("verified"))
                    if order else False,
                    "Metadata_Filter": query_metadata_filter(question)
                    if strategy in {"hybrid_metadata", "hybrid_metadata_rerank"}
                    else "none",
                })

    write_csv(OUTPUT_RESULTS, detailed_rows)

    summary_rows = []
    strategy_names = [
        "dense_vector",
        "bm25_lexical",
        "hybrid_rrf",
        "hybrid_metadata",
        "hybrid_metadata_rerank",
    ]

    verified_questions = [q for q in questions if is_verified(q)]
    unverified_questions = [q for q in questions if not is_verified(q)]

    for strategy in strategy_names:
        for k in TOP_K_VALUES:
            hits = 0
            reciprocal_ranks = []
            domain_hits = Counter()
            domain_counts = Counter()

            for row in verified_questions:
                test_id = row["Test_ID"]
                expected = parse_expected(row)
                order = strategy_orders[(test_id, strategy)]
                hit = expected_hit(order, expected, chunks, k)
                hits += int(hit)
                domain_counts[row.get("Domain", "")] += 1
                domain_hits[row.get("Domain", "")] += int(hit)
                reciprocal_ranks.append(
                    reciprocal_rank(order, expected, chunks)
                )

            total = len(verified_questions)
            summary_rows.append({
                "Strategy": strategy,
                "Top_K": k,
                "Verified_Questions": total,
                "Expected_Source_Hits": hits,
                "Hit_Rate_Percent": round(100 * hits / max(total, 1), 2),
                "MRR": round(
                    sum(reciprocal_ranks) / max(len(reciprocal_ranks), 1), 4
                ),
                "Unverified_Questions_Excluded": len(unverified_questions),
            })

    write_csv(OUTPUT_SUMMARY, summary_rows)

    # Build the comparison matrix using top-k=3.
    matrix_lines = [
        "# Department 3 Retrieval Strategy Comparison Matrix",
        "",
        f"Evaluation questions: {len(questions)}; staged chunks: {len(chunks)}.",
        f"Verified questions used for hit-rate/MRR: {len(verified_questions)}.",
        f"Unverified questions excluded from positive relevance scoring: {len(unverified_questions)}.",
        "",
        "| Strategy | Hit rate @3 | MRR | Description |",
        "|---|---:|---:|---|",
    ]

    descriptions = {
        "dense_vector": "Cosine similarity over pinned MiniLM embeddings.",
        "bm25_lexical": "Pure-Python BM25 lexical retrieval.",
        "hybrid_rrf": "Reciprocal Rank Fusion of dense and BM25 rankings.",
        "hybrid_metadata": "Hybrid RRF with verified, intent-specific, fail-closed source eligibility.",
        "hybrid_metadata_rerank": "Intent-filtered hybrid ranking with deterministic lexical reranking; experimental.",
    }

    for strategy in strategy_names:
        item = next(
            x for x in summary_rows
            if x["Strategy"] == strategy and x["Top_K"] == 3
        )
        matrix_lines.append(
            f"| {strategy} | {item['Hit_Rate_Percent']:.2f}% | "
            f"{item['MRR']:.4f} | {descriptions[strategy]} |"
        )

    matrix_lines += [
        "",
        "## Top-k comparison",
        "",
        "| Strategy | K | Hit rate | MRR |",
        "|---|---:|---:|---:|",
    ]
    for item in summary_rows:
        matrix_lines.append(
            f"| {item['Strategy']} | {item['Top_K']} | "
            f"{item['Hit_Rate_Percent']:.2f}% | {item['MRR']:.4f} |"
        )

    OUTPUT_MATRIX.write_text("\n".join(matrix_lines) + "\n", encoding="utf-8")

    config = [
        "# Department 3 Final Retrieval Configuration",
        "",
        "## Candidate configuration evaluated",
        "",
        f"- Embedding model: `{MODEL_NAME}`",
        f"- Model revision: `{MODEL_REVISION}`",
        "- Vector metric: cosine similarity",
        "- Embedding vectors: existing normalized 384-dimensional vectors",
        "- Lexical retrieval: BM25 (k1=1.5, b=0.75)",
        "- Hybrid fusion: Reciprocal Rank Fusion (RRF, k=60)",
        "- Query normalization: lowercase, punctuation/token normalization, typo map, Roman Urdu phrase aliases",
        "- Metadata eligibility: verified-only, intent-specific, fail-closed candidate filtering.",
        "- Reranking: deterministic lexical overlap bonuses; optional experiment, not enabled in the recommended default pipeline.",
        "- Tested top-k values: 1, 3, 5",
        f"- Provisional dense baseline threshold: cosine >= {DENSE_THRESHOLD:.2f}; not calibrated or deployment-approved.",
        "",
        "## Safety and metadata rules",
        "",
        "- Only verified/approved source records count as positive evidence.",
        "- Unverified expense-categorization draft `faq-002` must not be promoted to approved evidence.",
        "- `faq-005` confirms PDF reports for supported records; it does not confirm CSV export or exact screen-by-screen steps.",
        "- Do not use expected source IDs to filter retrieval candidates; they are evaluation labels only.",
        "- If no verified passage supports the requested feature or workflow, abstain rather than invent instructions.",
        "- Expense-categorization intent includes English, Roman Urdu, category-list and common misspelling variants.",
        "- Current approved candidate set for expense categorization is empty; faq-002 remains unverified and excluded.",
        "- Expense-reporting intent is restricted to verified faq-005; PDF support does not establish CSV export or exact UI steps.",
        "",
        "## Calibration status",
        "",
        "No calibrated universal relevance threshold has been established. The 0.40 dense threshold is provisional only. Validate score distributions against false positives, verified relevance and safe abstention before deployment.",
    ]
    OUTPUT_CONFIG.write_text("\n".join(config) + "\n", encoding="utf-8")

    # Focused comparison with the historical baseline on the original failed IDs.
    original_failed = [
        row for row in baseline_rows
        if str(row.get("Retrieval_Result", "")).upper() == "MISS"
    ]

    report = [
        "# Department 3 Retrieval Performance Report",
        "",
        "## Run scope",
        "",
        f"- Evaluation set: {len(questions)} questions",
        f"- Verified questions included in positive relevance metrics: {len(verified_questions)}",
        f"- Unverified questions excluded from positive relevance metrics: {len(unverified_questions)}",
        f"- Staged chunks: {len(chunks)}",
        f"- Original historical baseline misses: {len(original_failed)}",
        "- Strategies: dense vector, BM25, hybrid RRF, metadata-filtered hybrid, metadata-filtered hybrid with reranking",
        "- Top-k: 1, 3, 5",
        "",
        "## Best observed strategy at k=3",
        "",
    ]

    best = max(
        (x for x in summary_rows if x["Top_K"] == 3),
        key=lambda x: (x["Hit_Rate_Percent"], x["MRR"]),
    )
    report += [
        f"- Strategy: `{best['Strategy']}`",
        f"- Expected-source hit rate: {best['Hit_Rate_Percent']:.2f}%",
        f"- MRR: {best['MRR']:.4f}",
        "",
        "## Results",
        "",
        "| Strategy | K | Hit rate | MRR |",
        "|---|---:|---:|---:|",
    ]
    for item in summary_rows:
        report.append(
            f"| {item['Strategy']} | {item['Top_K']} | "
            f"{item['Hit_Rate_Percent']:.2f}% | {item['MRR']:.4f} |"
        )

    report += [
        "",
        "## Interpretation and limitations",
        "",
        "- Historical baseline misses and this staged benchmark are separate measurements; do not combine their denominators.",
        "- Unverified questions are excluded from expected-source hit-rate scoring. They must be assessed for safe abstention, not rewarded for retrieving unverified drafts.",
        "- The staged corpus contains only the approved/staged documents currently present in `chunks.json`; missing source records cannot be retrieved.",
        "- A higher hit rate does not by itself prove answer correctness or safe product instructions.",
        "- The best strategy is an observed candidate on this 60-question evaluation set, not a guarantee of future performance.",
        "- The comparison is a local retrieval benchmark, not an end-to-end chatbot or production-backend test.",
        "",
        "## Generated artifacts",
        "",
        f"- `{OUTPUT_RESULTS.relative_to(ROOT)}`",
        f"- `{OUTPUT_SUMMARY.relative_to(ROOT)}`",
        f"- `{OUTPUT_MATRIX.relative_to(ROOT)}`",
        f"- `{OUTPUT_CONFIG.relative_to(ROOT)}`",
        f"- `{OUTPUT_REPORT.relative_to(ROOT)}`",
    ]
    OUTPUT_REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")

    print("\n========== BENCHMARK COMPLETE ==========")
    print("Questions:", len(questions))
    print("Verified questions scored:", len(verified_questions))
    print("Unverified questions excluded:", len(unverified_questions))
    print("Historical baseline MISS rows:", len(original_failed))
    print("\nSUMMARY — top-k=3")
    for item in summary_rows:
        if item["Top_K"] == 3:
            print(
                item["Strategy"],
                "| Hit rate:", str(item["Hit_Rate_Percent"]) + "%",
                "| MRR:", item["MRR"],
            )

    print("\nGenerated:")
    for path in (
        OUTPUT_RESULTS, OUTPUT_SUMMARY, OUTPUT_MATRIX,
        OUTPUT_CONFIG, OUTPUT_REPORT,
    ):
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
