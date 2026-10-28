from pathlib import Path
import importlib.util

root = Path.cwd()
path = root / "src/financial_assistant/rag/retriever.py"
spec = importlib.util.spec_from_file_location("retrieval_eval", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
r = mod.FaqRetriever()

cases = [
    ("Overview", "HisabDo app features track money given received customer balances expenses PDF reports", {"faq-001"}),
    ("Categorize expense", "How to categorize classify assign an expense category in HisabDo", set()),
    ("Wrong prediction", "How to correct change or edit an incorrectly predicted expense category", set()),
    ("PDF report", "How to export or generate PDF reports for transactions expenses customer balances", {"faq-005"}),
    ("Income and expense totals", "How to view total income received money and expenses in the HisabDo app", set()),
    ("Add customer", "How to add or create a new customer and customer balance in HisabDo", set()),
    ("Record expense", "How to record or add a new expense transaction in HisabDo", set()),
]

def doc_id(d):
    return str(d.get("id", d.get("doc_id", d.get("faq_id", "unknown"))))

original = mod.RELEVANCE_THRESHOLD
lines = [
    "# Retrieval Parameter Sweep",
    "",
    f"- Verified documents: {len(r._docs)}",
    "- Queries tested: 7 rewritten Day 1 queries.",
    "- Method: existing verified-only TF-IDF cosine retrieval.",
    "- Target labels: faq-001 for overview and faq-005 for PDF reporting.",
    "- The other five questions have no confirmed exact workflow target in this evaluation.",
    "",
    "| Threshold | top_k | Overview target | PDF target | Queries with results | Total passages |",
    "|---:|---:|---|---|---:|---:|",
]
print("Verified documents:", len(r._docs))
print("\nThreshold | top_k | Overview hit | PDF hit | Queries with results | Passages")

try:
    for threshold in [0.12, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70]:
        mod.RELEVANCE_THRESHOLD = threshold
        for k in [1, 2, 3]:
            found = {}
            nonempty = 0
            total = 0
            for name, query, targets in cases:
                results = r.retrieve(query, top_k=k)
                ids = [doc_id(d) for d in results]
                found[name] = bool(targets.intersection(ids))
                nonempty += bool(results)
                total += len(results)
            row = (f"| {threshold:.2f} | {k} | "
                   f"{'Yes' if found['Overview'] else 'No'} | "
                   f"{'Yes' if found['PDF report'] else 'No'} | "
                   f"{nonempty}/7 | {total} |")
            lines.append(row)
            print(f"{threshold:.2f} | {k} | "
                  f"{found['Overview']} | {found['PDF report']} | "
                  f"{nonempty}/7 | {total}")

    mod.RELEVANCE_THRESHOLD = original
    lines += [
        "",
        "## Query inspection at threshold 0.12, top_k=3",
        "",
        "| Question | Returned documents and scores |",
        "|---|---|",
    ]
    for name, query, targets in cases:
        results = r.retrieve(query, top_k=3)
        desc = "; ".join(
            f"{doc_id(d)} ({d.get('title', 'Untitled')}, {d['score']:.4f})"
            for d in results
        ) or "No results"
        lines.append(f"| {name} | {desc} |")

finally:
    mod.RELEVANCE_THRESHOLD = original

lines += [
    "",
    "## Interpretation and limitations",
    "",
    "This sweep measures threshold and top_k effects on the existing verified-only TF-IDF retriever. The two target labels are limited to overview and PDF reporting. A returned result for the other five queries does not prove that it contains correct workflow instructions.",
    "",
    "This test does not evaluate semantic embeddings, hybrid retrieval, metadata-filter ablations, or reranking. No production threshold is declared optimal from these results alone. The missing workflow documents must be written and verified before claiming all seven questions are answerable.",
]
out = root / "docs/retrieval_parameter_sweep.md"
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\nSaved results:", out)
