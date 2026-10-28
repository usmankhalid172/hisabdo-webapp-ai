from pathlib import Path
import importlib.util

from src.financial_assistant.faq_rag import FaqRetriever

root = Path.cwd()
path = root / "src/financial_assistant/rag/retriever.py"
spec = importlib.util.spec_from_file_location("lexical_eval", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.RELEVANCE_THRESHOLD = 0.0

lexical = mod.FaqRetriever()
semantic = FaqRetriever(relevance_threshold=0.0)

queries = {
    "Overview": ("What can I do with HisabDo?", "faq-001"),
    "Categorize expense": ("How do I categorize an expense?", None),
    "Wrong prediction": ("What if the predicted category is wrong?", None),
    "PDF report": ("How do I generate a PDF report in HisabDo?", "faq-005"),
    "Income and expenses": ("How can I view my total income and expenses in HisabDo?", None),
    "Add customer": ("How do I add a new customer in HisabDo?", None),
    "Record expense": ("How do I record a new expense in HisabDo?", None),
}

def get_id(item):
    return str(item.get("id", item.get("doc_id", "unknown")))

def rank_results(results):
    ranked = {}
    for rank, item in enumerate(results, start=1):
        doc_id = get_id(item)
        ranked[doc_id] = {
            "rank": rank,
            "title": item.get("title", "Untitled"),
            "score": item.get("score", 0.0),
        }
    return ranked

print("LEXICAL vs SEMANTIC vs HYBRID (RRF)")
print("RRF formula: 1/(60 + lexical_rank) + 1/(60 + semantic_rank)")
print("No production files changed; original queries; top 3 per method.")
print("-" * 90)

for name, (query, target) in queries.items():
    lexical_results = lexical.retrieve(query, top_k=len(lexical._docs))
    semantic_results = semantic.retrieve(query, top_k=len(semantic.documents))

    lex = rank_results(lexical_results)
    sem = rank_results(semantic_results)

    fused = {}
    for doc_id in set(lex) | set(sem):
        score = 0.0
        if doc_id in lex:
            score += 1 / (60 + lex[doc_id]["rank"])
        if doc_id in sem:
            score += 1 / (60 + sem[doc_id]["rank"])
        fused[doc_id] = score

    hybrid_ids = sorted(fused, key=fused.get, reverse=True)[:3]

    def show(ids, lookup):
        if not ids:
            return "No results"
        return "; ".join(
            f"{doc_id}: {lookup[doc_id]['title']}"
            for doc_id in ids
        )

    lex_top = list(lex)[:3]
    sem_top = list(sem)[:3]

    print(f"\n{name}: {query}")
    print("  Lexical :", show(lex_top, lex))
    print("  Semantic:", show(sem_top, sem))
    print("  Hybrid  :", show(hybrid_ids, {
        doc_id: (
            lex.get(doc_id) or sem.get(doc_id) or {"title": "Untitled"}
        )
        for doc_id in hybrid_ids
    }))

    if target:
        print(
            f"  Target {target} in top 3 — "
            f"Lexical: {target in lex_top}, "
            f"Semantic: {target in sem_top}, "
            f"Hybrid: {target in hybrid_ids}"
        )

print("\nNote: Similarity/rank does not prove answer correctness.")
print("Five workflow queries still need verified relevance labels.")
