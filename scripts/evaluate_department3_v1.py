import json
from pathlib import Path
from collections import defaultdict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "department3_evaluation_v1.json"
FAQ = ROOT / "data" / "faq_docs.json"
KNOWLEDGE = ROOT / "data" / "sample_financial_knowledge.json"
OUTPUT = ROOT / "docs" / "department3_evaluation_v1_results.json"

def load_docs():
    docs = []
    for path in (FAQ, KNOWLEDGE):
        if path.exists():
            docs.extend(json.loads(path.read_text(encoding="utf-8")))
    unique = {}
    for doc in docs:
        if doc.get("id"):
            unique[doc["id"]] = doc
    return list(unique.values())

def main():
    dataset = json.loads(DATA.read_text(encoding="utf-8"))
    cases = dataset["cases"]
    docs = load_docs()

    corpus = [
        " ".join(str(doc.get(k, "")) for k in ("title", "text", "answer", "keywords"))
        for doc in docs
    ]
    vectorizer = TfidfVectorizer(
        stop_words="english", ngram_range=(1, 2), sublinear_tf=True
    )
    matrix = vectorizer.fit_transform(corpus)

    results = []
    answerable = []
    no_answer = []

    for case in cases:
        query = case["question"]
        expected = {
            ref.rsplit("#", 1)[-1]
            for ref in case["supporting_source_records"]
            if "#" in ref
        }
        scores = cosine_similarity(vectorizer.transform([query]), matrix)[0]
        ranked = sorted(
            [
                {"id": docs[i]["id"], "score": round(float(scores[i]), 4)}
                for i in range(len(docs))
            ],
            key=lambda item: item["score"],
            reverse=True,
        )
        top3 = ranked[:3]
        top1_id = top3[0]["id"] if top3 else None
        should_answer = case["expected_behavior"].startswith("answer")

        row = {
            "id": case["id"],
            "expected_behavior": case["expected_behavior"],
            "expected_source_ids": sorted(expected),
            "top1_id": top1_id,
            "top1_score": top3[0]["score"] if top3 else 0,
            "top3": top3,
            "hit_at_1": top1_id in expected if should_answer and expected else None,
            "hit_at_3": any(x["id"] in expected for x in top3)
                if should_answer and expected else None,
            "has_expected_source": bool(expected),
        }
        results.append(row)
        if should_answer and expected:
            answerable.append(row)
        elif not should_answer:
            no_answer.append(row)

    summary = {
        "dataset_version": dataset["version"],
        "total_cases": len(cases),
        "corpus_documents": len(docs),
        "answerable_cases_with_sources": len(answerable),
        "no_answer_or_clarification_cases": len(no_answer),
        "answerable_hit_at_1": round(
            sum(r["hit_at_1"] for r in answerable) / len(answerable), 4
        ) if answerable else None,
        "answerable_hit_at_3": round(
            sum(r["hit_at_3"] for r in answerable) / len(answerable), 4
        ) if answerable else None,
        "no_answer_cases_with_retrieved_source": sum(
            bool(r["top1_id"]) for r in no_answer
        ),
        "method": "TF-IDF unigram and bigram retrieval, top 3",
        "limitation": (
            "Retrieval-only evaluation. It does not score generated answers, "
            "citations, language quality, or safety. Cases without source IDs "
            "are excluded from hit-rate calculations."
        ),
    }

    output = {"summary": summary, "results": results}
    OUTPUT.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("Saved:", OUTPUT)

if __name__ == "__main__":
    main()
