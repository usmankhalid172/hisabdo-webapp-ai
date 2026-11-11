"""Compare portfolio query rewrites on the historical FAQ corpus.

Run from the repository root with:
    python scripts/evaluate_portfolio_query_rewrites.py

The corpus is retained for retrieval diagnostics only. It is not an approved
source for current portfolio answers; the application embedding index is not
used by this offline lexical benchmark.
"""
from __future__ import annotations

import evaluate_portfolio_retrieval as benchmark


CASES = (
    {
        "id": "industry-logistics",
        "query": "Have you done projects for logistics companies?",
        "rewrite_terms": ("transportation", "freight", "distribution", "supply chain"),
        "relevant_terms": ("logistics", "supply chain"),
    },
    {
        "id": "industry-healthtech",
        "query": "Do you have HealthTech case studies?",
        "rewrite_terms": ("healthcare", "medical", "patient", "telehealth"),
        "relevant_terms": ("healthcare", "telehealth"),
    },
    {
        "id": "industry-fintech-saas",
        "query": "Have you built FinTech or B2B SaaS products?",
        "rewrite_terms": ("financial technology", "billing", "subscription", "payments"),
        "relevant_terms": ("fintech", "billing", "subscription"),
    },
    {
        "id": "technology-hisabdo",
        "query": "Which framework and database power HisabDo?",
        "rewrite_terms": ("Flutter", "Supabase", "PostgreSQL"),
        "relevant_terms": ("Flutter, Supabase, and PostgreSQL",),
    },
)


def expanded_tokens(query: str, terms: tuple[str, ...]) -> list[str]:
    return benchmark.tokens(query) + [
        token for term in terms for token in benchmark.tokens(term)
    ]


def is_relevant(doc: dict[str, str], terms: tuple[str, ...]) -> bool:
    text = doc["text"].casefold()
    return any(term.casefold() in text for term in terms)


def rank_expansion(
    docs: list[dict[str, str]],
    query: str,
    rewrite_terms: tuple[str, ...],
    mode: str,
) -> list[tuple[float, dict[str, str]]]:
    rewritten = expanded_tokens(query, rewrite_terms)
    scored = []
    for doc in docs:
        doc_tokens = benchmark.tokens(doc["text"])
        if mode == "vector":
            score = benchmark.cosine(rewritten, doc_tokens)
        else:
            coverage = len(set(rewritten) & set(doc_tokens)) / max(len(set(rewritten)), 1)
            score = 0.65 * benchmark.cosine(rewritten, doc_tokens) + 0.35 * coverage
        scored.append((score, doc))
    return sorted(scored, key=lambda item: (-item[0], item[1]["id"]))


def main() -> None:
    docs = benchmark.load_docs()
    portfolio_docs = [
        doc for doc in docs if doc["url"].rstrip("/").endswith("/portfolio")
    ]
    print(
        f"Historical corpus: {len(docs)} FAQ facts; "
        f"{len(portfolio_docs)} portfolio facts; {len(CASES)} rewrite cases"
    )
    print("Scores are lexical proxies; no embedding model or application index is used.")
    print("Case | mode | top-2 relevant positions | hit@2 | precision@2")

    totals = {
        (mode, variant): {"hits": 0, "relevant": 0}
        for mode in ("vector", "hybrid")
        for variant in ("original", "expanded")
    }
    for case in CASES:
        for mode in ("vector", "hybrid"):
            for variant in ("original", "expanded"):
                terms = () if variant == "original" else case["rewrite_terms"]
                ranked = rank_expansion(
                    portfolio_docs, case["query"], terms, mode
                )[:2]
                matches = [
                    index
                    for index, (_, doc) in enumerate(ranked, start=1)
                    if is_relevant(doc, case["relevant_terms"])
                ]
                totals[(mode, variant)]["hits"] += bool(matches)
                totals[(mode, variant)]["relevant"] += len(matches)
                positions = ",".join(map(str, matches)) or "-"
                print(
                    f"{case['id']} | {mode} {variant} | {positions} | "
                    f"{int(bool(matches))} | {len(matches)}/2"
                )

    print("Aggregate over four diagnostic cases:")
    for mode in ("vector", "hybrid"):
        for variant in ("original", "expanded"):
            values = totals[(mode, variant)]
            print(
                f"{mode} {variant}: hit@2={values['hits'] / len(CASES):.3f} "
                f"precision@2={values['relevant'] / (2 * len(CASES)):.3f}"
            )

    print("Hybrid threshold sweep on expanded queries (portfolio-only, top_k=2):")
    for threshold in (0.10, 0.15, 0.20, 0.25, 0.30):
        hits = relevant_count = 0
        for case in CASES:
            ranked = [
                (score, doc)
                for score, doc in rank_expansion(
                    portfolio_docs, case["query"], case["rewrite_terms"], "hybrid"
                )
                if score >= threshold
            ][:2]
            matches = [
                doc for _, doc in ranked if is_relevant(doc, case["relevant_terms"])
            ]
            hits += bool(matches)
            relevant_count += len(matches)
        print(
            f"threshold={threshold:.2f} hit@2={hits / len(CASES):.3f} "
            f"precision@2={relevant_count / (2 * len(CASES)):.3f}"
        )


if __name__ == "__main__":
    main()
