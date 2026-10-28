from src.financial_assistant.faq_rag import FaqRetriever

queries = {
    "Overview": "What can I do with HisabDo?",
    "Categorize expense": "How do I categorize an expense?",
    "Wrong prediction": "What if the predicted category is wrong?",
    "PDF report": "How do I generate a PDF report in HisabDo?",
    "Income and expenses": "How can I view my total income and expenses in HisabDo?",
    "Add customer": "How do I add a new customer in HisabDo?",
    "Record expense": "How do I record a new expense in HisabDo?",
}

retriever = FaqRetriever(relevance_threshold=0.0)
thresholds = [0.0, 0.2, 0.4, 0.6, 0.8]

print(f"Verified documents loaded: {len(retriever.documents)}")
print("Raw top-3 results per original failed query")
print("-" * 75)

results_by_query = {}

for name, query in queries.items():
    results = retriever.retrieve(query, top_k=len(retriever.documents))
    results_by_query[name] = results
    print(f"\n{name}: {query}")

    for item in results[:3]:
        print(
            f"  {item['id']} | score={item['score']:.4f} | "
            f"{item['title']}"
        )

print("\nThreshold comparison: queries with at least one result")
print("Threshold | Queries with results | Total passages returned")

for threshold in thresholds:
    queries_with_results = 0
    total_passages = 0

    for results in results_by_query.values():
        kept = [item for item in results if item["score"] >= threshold]
        if kept:
            queries_with_results += 1
        total_passages += len(kept)

    print(
        f"{threshold:>9.1f} | {queries_with_results}/7"
        f"{'':>15} | {total_passages}"
    )
