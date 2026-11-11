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
CASES = json.loads(
    (ROOT / "data/department3_evaluation_v1.json").read_text(encoding="utf-8")
)["cases"]

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

corpus = [
    normalize(d.get("title", "") + " " + d.get("text", ""))
    for d in DOCS
]
vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
matrix = vectorizer.fit_transform(corpus)

token_docs = [tokens(doc) for doc in corpus]
frequencies = [Counter(doc) for doc in token_docs]
n = len(DOCS)
avg_len = sum(map(len, token_docs)) / max(n, 1)

def bm25_scores(query):
    query_terms = set(tokens(query))
    scores = []

    for document, freq in zip(token_docs, frequencies):
        score = 0.0
        length = len(document)

        for term in query_terms:
            df = sum(1 for item in frequencies if item[term] > 0)
            if not freq[term]:
                continue

            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
            denominator = freq[term] + 1.5 * (
                1 - 0.75 + 0.75 * length / max(avg_len, 1)
            )
            score += idf * freq[term] * 2.5 / denominator

        scores.append(score)

    return scores

FEATURE_INTENTS = {
    "export": {
        "query_terms": {
            "export", "exports", "download", "csv", "pdf", "report", "reports"
        },
        "document_terms": {
            "export", "exports", "download", "csv", "pdf", "report", "reports"
        },
    },
    "categorization": {
        "query_terms": {
            "categorize", "categorization", "category", "categories", "classify"
        },
        "document_terms": {
            "categorize", "categorization", "category", "categories", "classify"
        },
    },
}

rows = []

for case in CASES:
    query = case["question"]
    expected = [
        source.split("#")[-1]
        for source in case.get("supporting_source_records", [])
    ]

    expanded = expand(query)
    tfidf = cosine_similarity(
        vectorizer.transform([query]), matrix
    )[0].tolist()

    expanded_bm25 = bm25_scores(expanded)
    scaled_bm25 = [
        score / (score + 5.0) for score in expanded_bm25
    ]

    hybrid = [
        0.5 * scaled_bm25[i] + 0.5 * tfidf[i]
        for i in range(n)
    ]

    query_terms = set(tokens(query))
    intent_matches = []

    for i, doc in enumerate(DOCS):
        doc_terms = set(tokens(doc.get("title", "") + " " + doc.get("text", "")))
        matched = any(
            query_terms & intent["query_terms"]
            and doc_terms & intent["document_terms"]
            for intent in FEATURE_INTENTS.values()
        )
        intent_matches.append(matched)

    final_scores = [
        hybrid[i] + (0.20 if intent_matches[i] else 0.0)
        for i in range(n)
    ]

    ranked = sorted(
        range(n), key=lambda i: final_scores[i], reverse=True
    )
    top_index = ranked[0]
    top_id = DOCS[top_index]["id"]

    rows.append({
        "id": case["id"],
        "expected": expected,
        "score": final_scores[top_index],
        "top_id": top_id,
        "hit": bool(expected and top_id in expected),
    })

positive = [row for row in rows if row["expected"]]
negative = [row for row in rows if not row["expected"]]

print("=== FEATURE INTENT 0.20 THRESHOLD CALIBRATION ===")
print("Corpus documents:", len(DOCS))
print("Total cases:", len(rows))
print("Answerable cases:", len(positive))
print("No source cases:", len(negative))

thresholds = [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60]

for threshold in thresholds:
    accepted = [row for row in positive if row["score"] >= threshold]
    correct = sum(row["hit"] for row in accepted)
    false = [row for row in negative if row["score"] >= threshold]

    print(
        f"threshold={threshold:.2f}",
        f"coverage={len(accepted)}/{len(positive)}",
        f"precision={correct / len(accepted):.3f}" if accepted else "precision=N/A",
        f"false_accepts={len(false)}/{len(negative)}",
        f"IDs={[row['id'] for row in false]}"
    )

print("\n=== NO SOURCE CASE SCORES ===")
for row in negative:
    print(row["id"], f"{row['score']:.4f}", row["top_id"])

print("\n=== D3E028 VERIFICATION ===")
row = next(row for row in rows if row["id"] == "D3E028")
print(row)

print("\n=== D3E024 VERIFICATION ===")
row = next(row for row in rows if row["id"] == "D3E024")
print(row)
