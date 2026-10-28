import json
import re
import unicodedata
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "faq_docs.json"
OUTPUT_PATH = ROOT / "docs" / "faq_retrieval_evaluation_results.json"

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

SYNONYMS = {
    "revenue": ["income", "sales"],
    "expense": ["spending", "cost"],
    "expenses": ["spending", "costs"],
    "categorize": ["classify", "organize"],
    "categorization": ["classification"],
    "export": ["download", "pdf"],
    "download": ["export", "pdf"],
    "profit": ["earnings"],
    "track": ["record", "monitor"],
    "customer": ["client"],
}

def normalize(text):
    text = unicodedata.normalize("NFKC", text.lower())
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def expand_query(query):
    tokens = normalize(query).split()
    expanded = list(tokens)
    for token in tokens:
        expanded.extend(SYNONYMS.get(token, []))
    return " ".join(expanded)

def main():
    docs = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    corpus = [f"{d.get('title', '')} {d.get('text', '')}" for d in docs]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(corpus)

    variants = ["baseline", "normalized", "expanded", "expanded_reranked"]
    results = []

    for qid, query, expected in QUERIES:
        row = {
            "id": qid,
            "query": query,
            "expected_ids": expected,
            "approaches": {},
        }

        for variant in variants:
            search_query = query if variant == "baseline" else normalize(query)
            if variant in ("expanded", "expanded_reranked"):
                search_query = expand_query(query)

            scores = cosine_similarity(
                vectorizer.transform([search_query]), matrix
            )[0]
            terms = set(normalize(search_query).split())
            ranked = []

            for i, score in enumerate(scores):
                doc = docs[i]
                text = normalize(f"{doc.get('title', '')} {doc.get('text', '')}")
                title = normalize(doc.get("title", ""))
                text_terms = set(text.split())
                overlap = len(terms & text_terms) / max(len(terms), 1)
                title_overlap = len(terms & set(title.split())) / max(len(terms), 1)

                final_score = float(score)
                if variant == "expanded_reranked":
                    final_score = 0.65 * float(score) + 0.25 * overlap + 0.10 * title_overlap

                ranked.append({
                    "id": doc.get("id"),
                    "title": doc.get("title"),
                    "score": round(float(score), 4),
                    "final_score": round(final_score, 4),
                })

            ranked.sort(key=lambda x: x["final_score"], reverse=True)
            top3 = ranked[:3]
            top1 = top3[0]["id"] if top3 else None

            row["approaches"][variant] = {
                "top3": top3,
                "top1_id": top1,
                "hit_at_1": top1 in expected if expected else None,
                "hit_at_3": any(x["id"] in expected for x in top3) if expected else None,
                "top1_score": top3[0]["final_score"] if top3 else 0.0,
            }

        results.append(row)

    summary = {}
    for variant in variants:
        labeled = [r for r in results if r["expected_ids"] is not None]
        summary[variant] = {
            "answerable_queries": len(labeled),
            "hit_at_1": round(sum(r["approaches"][variant]["hit_at_1"] for r in labeled) / len(labeled), 4),
            "hit_at_3": round(sum(r["approaches"][variant]["hit_at_3"] for r in labeled) / len(labeled), 4),
        }

    threshold_sweep = {}
    for variant in variants:
        threshold_sweep[variant] = []
        for threshold in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]:
            answerable = [r for r in results if r["expected_ids"] is not None]
            no_answer = [r for r in results if r["expected_ids"] is None]
            accepted = [r for r in answerable if r["approaches"][variant]["top1_score"] >= threshold]
            correct = [r for r in accepted if r["approaches"][variant]["hit_at_1"]]
            false_accepts = [r for r in no_answer if r["approaches"][variant]["top1_score"] >= threshold]
            threshold_sweep[variant].append({
                "threshold": threshold,
                "coverage": round(len(accepted) / len(answerable), 4),
                "accepted_precision": round(len(correct) / len(accepted), 4) if accepted else None,
                "no_answer_false_accepts": len(false_accepts),
            })

    output = {
        "note": "Exploratory labeled proxy set; original Day 1 failed-query list was not located. TF-IDF and lexical query expansion are not embedding-based semantic retrieval.",
        "corpus_size": len(docs),
        "query_count": len(results),
        "summary": summary,
        "threshold_sweep": threshold_sweep,
        "results": results,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print("Corpus documents:", len(docs))
    print("Evaluation queries:", len(results))
    for name, metrics in summary.items():
        print(name, metrics)
    print("\nThreshold results:")
    for name, rows in threshold_sweep.items():
        print(name)
        for item in rows:
            print(item)
    print("\nSaved detailed results to:", OUTPUT_PATH)

if __name__ == "__main__":
    main()