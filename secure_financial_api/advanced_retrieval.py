
import json
import re
import math
from pathlib import Path
from collections import Counter

from knowledge_retrieval import get_model

BASE_DIR = Path(__file__).parent
FAQ_PATH = BASE_DIR / "knowledge_base" / "faq_cleaned.json"
METADATA_PATH = BASE_DIR / "knowledge_base" / "faq_metadata.json"

DEFAULT_TOP_K = 3
DEFAULT_THRESHOLD = 0.15
SEMANTIC_THRESHOLD = 0.45
UNRELATED_SEMANTIC_THRESHOLD = 0.55


def normalize_query(query):
    """Normalize English and Roman Urdu queries."""
    query = query.lower().strip()
    query = re.sub(r"[^\w\s]", " ", query)
    query = re.sub(r"\s+", " ", query)

    replacements = {
        "baqi": "outstanding",
        "bacha": "remaining",
        "paisa": "money",
        "paise": "money",
        "kitna": "how much",
        "mere": "my",
        "karna": "do",
        "supplier": "payable",
        "suppliers": "payable",
    }

    words = [replacements.get(word, word) for word in query.split()]
    return " ".join(words)


def load_data():
    with open(FAQ_PATH, encoding="utf-8") as file:
        faq_data = json.load(file)

    with open(METADATA_PATH, encoding="utf-8") as file:
        metadata_data = json.load(file)

    metadata = {
        item["faq_id"]: item
        for item in metadata_data["chunks"]
    }

    documents = [
        doc for doc in faq_data["documents"]
        if doc.get("verified") is True
    ]

    return documents, metadata


STOP_WORDS = {
    "what", "is", "the", "a", "an", "my", "me",
    "do", "i", "how", "much", "for", "to", "of",
    "and", "in", "on", "your", "business", "like"
}

WORD_MAP = {
    "suppliers": "supplier",
    "supplied": "supplier",
    "owes": "owe",
    "owed": "owe",
    "customers": "customer",
    "baqi": "outstanding",
    "paisa": "money",
    "paise": "money"
}


def tokenize(text):
    words = re.findall(r"\b\w+\b", text.lower())

    return [
        WORD_MAP.get(word, word)
        for word in words
        if word not in STOP_WORDS
    ]


def lexical_search(query, documents):
    """Calculate BM25-style lexical relevance scores."""
    query_tokens = tokenize(query)

    doc_tokens = {
        doc["id"]: tokenize(
            doc["title"] + " " +
            doc["question"] + " " +
            doc["answer"]
        )
        for doc in documents
    }

    total_docs = len(documents)
    avg_length = (
        sum(map(len, doc_tokens.values())) / max(total_docs, 1)
    )

    scores = {}

    for doc_id, tokens in doc_tokens.items():
        frequencies = Counter(tokens)
        length = len(tokens)
        score = 0.0

        for term in query_tokens:
            frequency = frequencies[term]

            if frequency == 0:
                continue

            document_frequency = sum(
                term in set(other_tokens)
                for other_tokens in doc_tokens.values()
            )

            idf = math.log(
                1 + (total_docs - document_frequency + 0.5) /
                (document_frequency + 0.5)
            )

            k1 = 1.5
            b = 0.75

            denominator = frequency + k1 * (
                1 - b + b * length / max(avg_length, 1)
            )

            score += idf * (
                frequency * (k1 + 1) / denominator
            )

        scores[doc_id] = score

    return scores


def retrieve(
    query,
    method="hybrid",
    top_k=DEFAULT_TOP_K,
    threshold=DEFAULT_THRESHOLD,
    product_area=None,
):
    """Retrieve, filter, combine and rerank relevant FAQ documents."""

    if method not in ("semantic", "lexical", "hybrid"):
        raise ValueError(
            "Method must be semantic, lexical, or hybrid."
        )

    documents, metadata = load_data()
    normalized_query = normalize_query(query)

    if product_area:
        documents = [
            doc for doc in documents
            if metadata.get(doc["id"], {}).get("product_area")
            == product_area
        ]

    if not documents:
        return []

    # Step 1: Calculate lexical scores.
    lexical_scores = lexical_search(normalized_query, documents)
    max_lexical = max(lexical_scores.values(), default=0.0)

    # Step 2: Calculate semantic scores for every document.
    model = get_model()

    query_embedding = model.encode(
        [normalized_query],
        normalize_embeddings=True
    )[0]

    document_texts = [
        doc["title"] + " " + doc["question"] + " " + doc["answer"]
        for doc in documents
    ]

    document_embeddings = model.encode(
        document_texts,
        normalize_embeddings=True
    )

    results = []

    for index, doc in enumerate(documents):
        doc_id = doc["id"]

        semantic_score = float(
            sum(
                a * b
                for a, b in zip(
                    query_embedding,
                    document_embeddings[index]
                )
            )
        )

        lexical_score = (
            lexical_scores.get(doc_id, 0.0) / max_lexical
            if max_lexical > 0 else 0.0
        )

        # Step 3: Select retrieval method.
        if method == "semantic":
            score = semantic_score
        elif method == "lexical":
            score = lexical_score
        else:
            score = (
                0.5 * semantic_score +
                0.5 * lexical_score
            )

        # Step 4: Rerank using title and question relevance.
        query_words = set(tokenize(normalized_query))

        title_question = set(
            tokenize(doc["title"] + " " + doc["question"])
        )

        overlap = (
            len(query_words & title_question) /
            max(len(query_words), 1)
        )

        rerank_score = 0.8 * score + 0.2 * overlap

        # Step 5: Reject unrelated queries.
        if method == "semantic":
            if semantic_score < SEMANTIC_THRESHOLD:
                continue

        elif method == "lexical":
            if lexical_score == 0:
                continue

        else:
            if (
                lexical_score == 0
                and semantic_score < UNRELATED_SEMANTIC_THRESHOLD
            ):
                continue

        minimum_score = (
            SEMANTIC_THRESHOLD
            if method == "semantic"
            else threshold
        )

        if rerank_score < minimum_score:
            continue

        results.append({
            "document_id": doc_id,
            "answer": doc["answer"],
            "source": doc["source"],
            "score": round(score, 4),
            "rerank_score": round(rerank_score, 4),
            "metadata": metadata.get(doc_id, {}),
        })

    results.sort(
        key=lambda item: item["rerank_score"],
        reverse=True
    )

    return results[:top_k]


def precision_at_k(retrieved, relevant, k):
    selected = retrieved[:k]

    if k <= 0:
        return 0.0

    return sum(item in relevant for item in selected) / k


def recall_at_k(retrieved, relevant, k):
    if not relevant:
        return 0.0

    return sum(
        item in relevant for item in retrieved[:k]
    ) / len(relevant)


def reciprocal_rank(retrieved, relevant):
    for rank, item in enumerate(retrieved, start=1):
        if item in relevant:
            return 1 / rank

    return 0.0


def ndcg_at_k(retrieved, relevant, k):
    dcg = sum(
        1 / math.log2(rank + 1)
        for rank, item in enumerate(retrieved[:k], start=1)
        if item in relevant
    )

    ideal_count = min(len(relevant), k)

    idcg = sum(
        1 / math.log2(rank + 1)
        for rank in range(1, ideal_count + 1)
    )

    return dcg / idcg if idcg else 0.0


if __name__ == "__main__":
    question = input("Enter a question: ")

    for method in ("semantic", "lexical", "hybrid"):
        print(f"\n--- {method.upper()} ---")

        results = retrieve(question, method=method)

        if not results:
            print("No relevant results found.")
            continue

        for result in results:
            print(
                result["document_id"],
                result["score"],
                result["answer"]
            )
