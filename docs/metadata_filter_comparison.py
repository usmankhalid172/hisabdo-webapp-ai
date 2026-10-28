import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

docs = json.loads(Path("data/faq_docs.json").read_text(encoding="utf-8"))

queries = [
    ("Overview", "What can I do with HisabDo?", "faq-001"),
    ("Categorize expense", "How do I categorize an expense?", None),
    ("Wrong prediction", "What if the predicted category is wrong?", None),
    ("PDF report", "How do I generate a PDF report in HisabDo?", "faq-005"),
    ("Income and expenses", "How can I view my total income and expenses in HisabDo?", None),
    ("Add customer", "How do I add a new customer in HisabDo?", None),
    ("Record expense", "How do I record a new expense in HisabDo?", None),
]

def evaluate(corpus, label):
    corpus = [d for d in corpus if isinstance(d, dict)]
    if not corpus:
        print(label, ": no documents")
        return
    texts = [f"{d.get('title', '')} {d.get('text', '')}" for d in corpus]
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(texts)
    print(f"\n{label} ({len(corpus)} documents)")
    for name, query, target in queries:
        scores = cosine_similarity(vectorizer.transform([query]), matrix)[0]
        idx = scores.argsort()[::-1][:1]
        best = corpus[int(idx[0])]
        hit = "TARGET HIT" if target and best.get("id") == target else (
            "TARGET MISS" if target else "UNLABELLED")
        print(f"{name}: {best.get('id')} | {scores[int(idx[0])]:.4f} | {best.get('category')} | {hit}")

evaluate([d for d in docs if isinstance(d, dict) and d.get("verified") is True], "Verified-only baseline")
evaluate([d for d in docs if isinstance(d, dict)], "All documents (filter removed)")
evaluate([d for d in docs if isinstance(d, dict) and d.get("verified") is True and d.get("category") == "Product Support"], "Verified Product Support only")
