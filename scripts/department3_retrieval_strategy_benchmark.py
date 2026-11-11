import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parents[1]
DOCS = json.loads((ROOT / "data/faq_docs.json").read_text(encoding="utf-8"))
DATA = json.loads((ROOT / "data/department3_evaluation_v1.json").read_text(encoding="utf-8"))
CASES = DATA["cases"]

OUTPUT = ROOT / "docs/department3_retrieval_benchmark_results.json"
TOP_K = [1, 3, 5]

SYNONYMS = {
    "revenue": ["income", "sales"],
    "income": ["revenue", "earnings"],
    "expense": ["spending", "cost"],
    "expenses": ["spending", "costs"],
    "categorize": ["classify", "organize"],
    "categorization": ["classification"],
    "export": ["download", "report"],
    "exports": ["export", "download"],
    "download": ["export", "report"],
    "profit": ["earnings"],
    "cash": ["money"],
    "flow": ["movement"],
    "customer": ["client"],
    "balance": ["outstanding", "owed"],
    "business": ["company"],
}

def normalize(text):
    text = unicodedata.normalize("NFKC", str(text).lower())
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def tokens(text):
    return normalize(text).split()

def expand(text):
    words = tokens(text)
    result = list(words)
    for word in words:
        result.extend(SYNONYMS.get(word, []))
    return " ".join(result)

def bm25_scores(query, documents, k1=1.5, b=0.75):
    token_docs = [tokens(doc) for doc in documents]
    query_terms = set(tokens(query))
    n = len(token_docs)
    avg_len = sum(map(len, token_docs)) / max(n, 1)
    frequencies = [Counter(doc) for doc in token_docs]
    scores = []

    for doc, freq in zip(token_docs, frequencies):
        score = 0.0
        length = len(doc)
        for term in query_terms:
            df = sum(1 for item in frequencies if item[term] > 0)
            if not freq[term]:
                continue
            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
            denominator = freq[term] + k1 * (
                1 - b + b * length / max(avg_len, 1)
            )
            score += idf * freq[term] * (k1 + 1) / denominator
        scores.append(score)
    return scores

corpus = [
    normalize(d.get("title", "") + " " + d.get("text", ""))
    for d in DOCS
]
vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
matrix = vectorizer.fit_transform(corpus)

def metadata_candidates(query):
    q = normalize(query)
    if any(x in q for x in ["privacy", "private", "train", "data"]):
        return [i for i, d in enumerate(DOCS)
                if d.get("product_area") == "HisabDo Privacy"]
    if any(x in q for x in ["hisabdo", "app", "expense", "export",
                            "categor", "customer", "business"]):
        return [i for i, d in enumerate(DOCS)
                if d.get("product_area") == "HisabDo"]
    return list(range(len(DOCS)))

def rank_query(query):
    normalized = normalize(query)
    expanded = expand(query)

    tfidf = cosine_similarity(
        vectorizer.transform([query]), matrix
    )[0].tolist()

    normalized_tfidf = cosine_similarity(
        vectorizer.transform([normalized]), matrix
    )[0].tolist()

    bm25 = bm25_scores(query, corpus)
    expanded_bm25 = bm25_scores(expanded, corpus)

    bm25_scaled = [x / (x + 5.0) for x in bm25]
    expanded_bm25_scaled = [
        x / (x + 5.0) for x in expanded_bm25
    ]

    hybrid = [
        0.5 * bm25_scaled[i] + 0.5 * tfidf[i]
        for i in range(len(DOCS))
    ]

    expanded_hybrid = [
        0.5 * expanded_bm25_scaled[i] + 0.5 * tfidf[i]
        for i in range(len(DOCS))
    ]

    query_terms = set(tokens(expanded))
    reranked = []
    for i, doc in enumerate(DOCS):
        doc_terms = set(tokens(corpus[i]))
        title_terms = set(tokens(doc.get("title", "")))
        overlap = len(query_terms & doc_terms) / max(len(query_terms), 1)
        title_overlap = len(query_terms & title_terms) / max(len(query_terms), 1)
        reranked.append(
            0.75 * expanded_hybrid[i] + 0.20 * overlap + 0.05 * title_overlap
        )

    filtered_ids = metadata_candidates(query)
    filtered = [
        expanded_hybrid[i] if i in filtered_ids else -1.0
        for i in range(len(DOCS))
    ]

    feature_intents = {
        "export": {
            "query_terms": {"export", "exports", "download", "csv", "pdf", "report", "reports"},
            "document_terms": {"export", "exports", "download", "csv", "pdf", "report", "reports"},
        },
        "categorization": {
            "query_terms": {"categorize", "categorization", "category", "categories", "classify"},
            "document_terms": {"categorize", "categorization", "category", "categories", "classify"},
        },
    }

    query_token_set = set(tokens(query))
    intent_scores = [0.0] * len(DOCS)

    for intent in feature_intents.values():
        if query_token_set & intent["query_terms"]:
            for i, doc in enumerate(DOCS):
                doc_text = normalize(doc.get("title", "") + " " + doc.get("text", ""))
                doc_terms = set(tokens(doc_text))
                if doc_terms & intent["document_terms"]:
                    intent_scores[i] = 0.05

    feature_intent_reranked = [
        expanded_hybrid[i] + intent_scores[i]
        for i in range(len(DOCS))
    ]

    feature_intent_015 = [
        expanded_hybrid[i] + (0.15 if intent_scores[i] > 0 else 0.0)
        for i in range(len(DOCS))
    ]
    feature_intent_020 = [
        expanded_hybrid[i] + (0.20 if intent_scores[i] > 0 else 0.0)
        for i in range(len(DOCS))
    ]
    feature_intent_025 = [
        expanded_hybrid[i] + (0.25 if intent_scores[i] > 0 else 0.0)
        for i in range(len(DOCS))
    ]

    variants = {
        "tfidf_baseline": tfidf,
        "normalized_tfidf": normalized_tfidf,
        "bm25": bm25,
        "bm25_tfidf_hybrid": hybrid,
        "expanded_hybrid": expanded_hybrid,
        "expanded_hybrid_reranked": reranked,
        "metadata_filtered_hybrid": filtered,
        "feature_intent_reranked": feature_intent_reranked,
        "feature_intent_015": feature_intent_015,
        "feature_intent_020": feature_intent_020,
        "feature_intent_025": feature_intent_025,
    }

    output = {}
    for name, scores in variants.items():
        indices = sorted(range(len(DOCS)), key=lambda i: scores[i], reverse=True)
        output[name] = [
            {
                "id": DOCS[i]["id"],
                "score": round(float(scores[i]), 6),
                "product_area": DOCS[i].get("product_area"),
                "title": DOCS[i].get("title"),
            }
            for i in indices[:5]
            if scores[i] >= 0
        ]
    return output

def expected_ids(case):
    return [
        item.split("#")[-1]
        for item in case.get("supporting_source_records", [])
    ]

results = []
for case in CASES:
    expected = expected_ids(case)
    ranked = rank_query(case["question"])
    row = {
        "case_id": case["id"],
        "question": case["question"],
        "domain": case["domain"],
        "language": case["language"],
        "expected_behavior": case["expected_behavior"],
        "expected_ids": expected,
        "retrieval_applicable": bool(expected),
        "strategies": {},
    }

    for strategy, items in ranked.items():
        ids = [x["id"] for x in items]
        row["strategies"][strategy] = {
            "top_results": items,
            "hit_at_1": bool(expected and ids[:1] and ids[0] in expected),
            "hit_at_3": bool(expected and set(ids[:3]) & set(expected)),
            "hit_at_5": bool(expected and set(ids[:5]) & set(expected)),
        }
    results.append(row)

strategy_names = list(results[0]["strategies"])
answerable = [r for r in results if r["retrieval_applicable"]]
no_source = [r for r in results if not r["retrieval_applicable"]]

summary = {}
for name in strategy_names:
    summary[name] = {
        "answerable_cases": len(answerable),
        "hit_at_1": round(sum(r["strategies"][name]["hit_at_1"] for r in answerable) / len(answerable), 4),
        "hit_at_3": round(sum(r["strategies"][name]["hit_at_3"] for r in answerable) / len(answerable), 4),
        "hit_at_5": round(sum(r["strategies"][name]["hit_at_5"] for r in answerable) / len(answerable), 4),
        "no_source_cases": len(no_source),
    }

day1_ids = {"D3E004", "D3E014", "D3E024", "D3E028", "D3E042", "D3E043"}
day1_results = [
    r for r in results if r["case_id"] in day1_ids
]

report = {
    "title": "Department 3 Retrieval Strategy Benchmark",
    "dataset_cases": len(CASES),
    "corpus_documents": len(DOCS),
    "answerable_source_cases": len(answerable),
    "no_source_cases": len(no_source),
    "embedding_status": "NOT MEASURED: no dense embedding model installed",
    "bm25_status": "Local BM25 implementation, not rank_bm25",
    "hybrid_definition": "Normalized BM25 and TF-IDF scores combined with equal weights",
    "metadata_filter_note": "Heuristic product area filter, experimental only",
    "reranking_note": "Lexical overlap reranker, not a learned cross encoder",
    "summary": summary,
    "day1_failure_cases": day1_results,
    "all_results": results,
}

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(
    json.dumps(report, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("Benchmark completed.")
print("Dataset cases:", len(CASES))
print("Corpus documents:", len(DOCS))
print("Answerable cases:", len(answerable))
print("No source cases:", len(no_source))
print("\nStrategy results:")
for name, metrics in summary.items():
    print(name, metrics)
print("\nDay 1 failure cases:")
for item in day1_results:
    print(item["case_id"], item["question"])
    for name in strategy_names:
        result = item["strategies"][name]
        print(" ", name, "Top 1:", result["top_results"][0]["id"] if result["top_results"] else "None",
              "Hit@3:", result["hit_at_3"])
print("\nSaved:", OUTPUT)
