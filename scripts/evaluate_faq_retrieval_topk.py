import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "faq_docs.json"
OUTPUT_PATH = ROOT / "docs" / "faq_retrieval_topk_results.json"

QUERIES = [
    ("E01", "What is HisabDo?", ["faq-001"]),
    ("E02", "How does automatic expense categorization work?", ["faq-002"]),
    ("E03", "Is my financial data used to train the shared AI model?", ["faq-003"]),
    ("E04", "What is a cash flow statement?", ["faq-004"]),
    ("E05", "How do I export my expenses?", ["faq-005"]),
    ("E06", "What is the difference between profit and cash flow?", ["faq-006"]),
    ("E07", "What is revenue?", ["finance_002"]),
    ("E08", "What is an expense?", ["finance_003"]),
    ("E09", "What is cash flow?", ["finance_004"]),
    ("E10", "Why should customer balances be tracked?", ["finance_005"]),
    ("W01", "What does revenue mean?", ["finance_002"]),
    ("W02", "Why categorize business expenses?", ["finance_006"]),
    ("W03", "What reports show money coming in and going out?", ["faq-004", "finance_004"]),
    ("W04", "How do I track business spending?", ["finance_006", "finance_003"]),
    ("W05", "What is the money left after paying costs?", ["finance_001"]),
    ("W06", "How can I download my expense report?", ["faq-005"]),
    ("N01", "What is my current account balance?", None),
    ("N02", "Tell me another customer's balance.", None),
    ("N03", "What is the weather today?", None),
    ("N04", "How do I add a payable?", None),
]

def main():
    docs = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    corpus = [f"{d.get('title', '')} {d.get('text', '')}" for d in docs]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(corpus)

    results = []
    for qid, query, expected in QUERIES:
        scores = cosine_similarity(vectorizer.transform([query]), matrix)[0]
        ranked_indices = scores.argsort()[::-1]
        ranked = [
            {
                "id": docs[i].get("id"),
                "title": docs[i].get("title"),
                "score": round(float(scores[i]), 4),
                "product_area": docs[i].get("product_area"),
            }
            for i in ranked_indices
        ]

        # Test top-k values and whether the expected answer appears in the results.
        topk_metrics = {}
        for k in [1, 2, 3, 5]:
            top = ranked[:k]
            topk_metrics[str(k)] = {
                "returned_ids": [x["id"] for x in top],
                "hit": (
                    any(x["id"] in expected for x in top)
                    if expected is not None else None
                ),
            }

        # Metadata-filter experiment: retain only explicit HisabDo product/privacy docs.
        # General financial concepts are not filtered because they may be valid FAQ answers.
        filtered_docs = [
            d for d in docs
            if d.get("product_area") in ("HisabDo", "HisabDo Privacy")
        ]
        filtered_corpus = [
            f"{d.get('title', '')} {d.get('text', '')}" for d in filtered_docs
        ]
        filtered_vectorizer = TfidfVectorizer(
            stop_words="english", ngram_range=(1, 2)
        )
        filtered_matrix = filtered_vectorizer.fit_transform(filtered_corpus)
        filtered_scores = cosine_similarity(
            filtered_vectorizer.transform([query]), filtered_matrix
        )[0]
        filtered_ranked = [
            {
                "id": filtered_docs[i].get("id"),
                "title": filtered_docs[i].get("title"),
                "score": round(float(filtered_scores[i]), 4),
            }
            for i in filtered_scores.argsort()[::-1]
        ][:3]

        results.append({
            "query_id": qid,
            "query": query,
            "expected_ids": expected,
            "baseline_topk": topk_metrics,
            "metadata_filter_top3": filtered_ranked,
            "metadata_filter_hit_at_3": (
                any(x["id"] in expected for x in filtered_ranked)
                if expected is not None else None
            ),
        })

    answerable = [r for r in results if r["expected_ids"] is not None]
    summary = {}
    for k in [1, 2, 3, 5]:
        hits = sum(r["baseline_topk"][str(k)]["hit"] for r in answerable)
        summary[f"baseline_hit_at_{k}"] = round(hits / len(answerable), 4)

    metadata_hits = sum(
        r["metadata_filter_hit_at_3"] for r in answerable
    )
    summary["metadata_filter_hit_at_3"] = round(
        metadata_hits / len(answerable), 4
    )

    output = {
        "note": (
            "Exploratory evaluation using 20 labeled proxy questions. "
            "Original Day 1 failure list was not located. Metadata filtering "
            "was tested only as an experiment, not applied to production."
        ),
        "corpus_size": len(docs),
        "query_count": len(results),
        "answerable_query_count": len(answerable),
        "summary": summary,
        "results": results,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("Corpus documents:", len(docs))
    print("Queries:", len(results))
    print("Summary:", summary)
    print("Saved results to:", OUTPUT_PATH)

if __name__ == "__main__":
    main()