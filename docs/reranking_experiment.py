from pathlib import Path

from src.financial_assistant.faq_rag import FaqRetriever

QUERIES = {
    "Overview": "What can I do with HisabDo?",
    "Categorize expense": "How do I categorize an expense?",
    "Wrong prediction": "What if the predicted category is wrong?",
    "PDF report": "How do I generate a PDF report in HisabDo?",
    "Income and expenses": "How can I view my total income and expenses in HisabDo?",
    "Add customer": "How do I add a new customer in HisabDo?",
    "Record expense": "How do I record a new expense in HisabDo?",
}

OUTPUT = Path("docs/reranking_experiment.md")
retriever = FaqRetriever(relevance_threshold=0.0)

def rerank(query, candidates):
    """Lightweight query-term reranking diagnostic, not a trained reranker."""
    terms = set(query.lower().replace("?", "").split())

    def score(item):
        text = (item["title"] + " " + item["text"]).lower()
        overlap = sum(1 for term in terms if term in text)
        return overlap

    return sorted(
        candidates,
        key=lambda item: (score(item), item["score"]),
        reverse=True,
    )

lines = [
    "# Reranking Experiment",
    "",
    "Diagnostic comparison of semantic ranking against simple query-term reranking.",
    "",
    "Important: query-term overlap is a lightweight heuristic, not a trained cross-encoder.",
    "Scores are diagnostic only. Ranking position does not prove answer correctness.",
    "Only verified knowledge-base documents are retrieved.",
    "",
]

print("Semantic ranking vs query-term reranking")
print("-" * 72)

for name, query in QUERIES.items():
    candidates = retriever.retrieve(query, top_k=len(retriever.documents))
    reranked = rerank(query, candidates)

    lines.extend([f"## {name}", "", f"Query: {query}", ""])

    print(f"\n{name}: {query}")
    print("Original top 3:")
    for rank, item in enumerate(candidates[:3], start=1):
        print(f"  {rank}. {item['id']} | {item['title']} | similarity={item['score']:.4f}")
        lines.append(
            f"- Original {rank}: `{item['id']}` — {item['title']} "
            f"(similarity={item['score']:.4f})"
        )

    print("Reranked top 3:")
    for rank, item in enumerate(reranked[:3], start=1):
        overlap = sum(
            1 for term in set(query.lower().replace("?", "").split())
            if term in (item["title"] + " " + item["text"]).lower()
        )
        print(f"  {rank}. {item['id']} | {item['title']} | term_overlap={overlap}")
        lines.append(
            f"- Reranked {rank}: `{item['id']}` — {item['title']} "
            f"(term overlap={overlap})"
        )

    lines.append("")

lines.extend([
    "## Limitations",
    "",
    "- This is a heuristic reranking diagnostic, not a trained neural reranker.",
    "- Five workflow queries do not yet have confirmed relevance labels.",
    "- A reranker cannot supply missing verified workflow instructions.",
    "- Do not select a production winner without human relevance judgments and an irrelevant-context check.",
    "",
])

OUTPUT.write_text("\n".join(lines), encoding="utf-8")
print(f"\nSaved results to: {OUTPUT}")
