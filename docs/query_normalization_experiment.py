import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

kb_path = Path("data/faq_docs.json")
docs = json.loads(kb_path.read_text(encoding="utf-8"))
docs = [d for d in docs if d.get("verified") is True]

queries = [
    ("What can I do with HisabDo?",
     "HisabDo features functions capabilities"),
    ("How do I categorize an expense?",
     "categorize classify assign expense category"),
    ("What if the predicted category is wrong?",
     "incorrect wrong prediction change correct expense category"),
    ("How do I generate a PDF report in HisabDo?",
     "create generate export download PDF report"),
    ("How can I view my total income and expenses in HisabDo?",
     "view dashboard total income expenses summary"),
    ("How do I add a new customer in HisabDo?",
     "add create new customer client"),
    ("How do I record a new expense in HisabDo?",
     "record add enter save new expense transaction"),
]

texts = [
    f"{d.get('title', '')} {d.get('text', '')}"
    for d in docs
]
vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True)
matrix = vectorizer.fit_transform(texts)

print(f"Verified documents: {len(docs)}")
print("Comparison: original query vs synonym-expanded query")
print("=" * 72)

for original, rewritten in queries:
    original_vec = vectorizer.transform([original])
    rewritten_vec = vectorizer.transform([original + " " + rewritten])
    original_scores = cosine_similarity(original_vec, matrix)[0]
    rewritten_scores = cosine_similarity(rewritten_vec, matrix)[0]

    def top_results(scores):
        ranked = scores.argsort()[::-1][:3]
        return [
            f"{docs[i].get('id')} ({scores[i]:.3f}) "
            f"{docs[i].get('title', '')}"
            for i in ranked
        ]

    print(f"\nQUERY: {original}")
    print("ORIGINAL:")
    for item in top_results(original_scores):
        print("  ", item)
    print("EXPANDED:")
    for item in top_results(rewritten_scores):
        print("  ", item)
