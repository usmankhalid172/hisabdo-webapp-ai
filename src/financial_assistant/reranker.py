import re
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS


def _terms(text):
    return {
        word for word in re.findall(r"\w+", text.lower())
        if word not in ENGLISH_STOP_WORDS and len(word) > 1
    }


def rerank_results(query, results):
    query_terms = _terms(query)

    if not query_terms or not results:
        return list(results)

    reranked = []

    for original_rank, item in enumerate(results, start=1):
        title_terms = _terms(item.get("title", ""))
        body_terms = _terms(item.get("text", ""))

        title_coverage = len(query_terms & title_terms) / len(query_terms)
        body_coverage = len(query_terms & body_terms) / len(query_terms)

        rerank_score = (
            0.70 * title_coverage
            + 0.30 * body_coverage
        )

        result = dict(item)
        result["original_rank"] = original_rank
        result["rerank_score"] = round(rerank_score, 4)
        reranked.append(result)

    return sorted(
        reranked,
        key=lambda item: (
            -item["rerank_score"],
            -item.get("hybrid_score", item.get("score", 0)),
            item["original_rank"],
        ),
    )
