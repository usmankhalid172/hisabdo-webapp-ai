
"""
Semantic search for the Finance Knowledge Base.
Uses multilingual embeddings, a relevance threshold, and source attribution.
"""

import json
from pathlib import Path

from sentence_transformers import SentenceTransformer


# Paths are based on this file's location, not the terminal's folder.
KB_PATH = Path(__file__).parent / "knowledge_base" / "faq.json"

# This model supports multilingual semantic search, including many Urdu/English
# mixed-language queries. The model downloads the first time it is used.
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Initial threshold: evaluate and tune this using real test questions.
DEFAULT_THRESHOLD = 0.45

FALLBACK_ANSWER = (
    "I couldn't find a sufficiently relevant, verified answer in the "
    "Knowledge Base. Please rephrase your question or contact support."
)

_model = None


def get_model():
    """Load the embedding model once and reuse it."""
    global _model

    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)

    return _model


def load_knowledge_base():
    """Load the versioned Knowledge Base and keep verified entries with sources."""
    with KB_PATH.open("r", encoding="utf-8-sig") as file:
        knowledge_base = json.load(file)

    documents = [
        document
        for document in knowledge_base.get("documents", [])
        if document.get("verified") is True
        and document.get("source")
        and document.get("question")
        and document.get("answer")
    ]

    return knowledge_base.get("kb_version", "unknown"), documents


def search_knowledge_base(
    question: str,
    threshold: float = DEFAULT_THRESHOLD,
) -> dict:
    """Find the most relevant verified FAQ or return a safe fallback."""
    if not question or not question.strip():
        return {
            "found": False,
            "answer": FALLBACK_ANSWER,
            "source": None,
            "score": None,
            "kb_version": None,
        }

    kb_version, documents = load_knowledge_base()

    if not documents:
        return {
            "found": False,
            "answer": FALLBACK_ANSWER,
            "source": None,
            "score": None,
            "kb_version": kb_version,
        }

    model = get_model()

    
    # Represent each FAQ using its full context and its question separately.
    # Comparing separately helps short or mixed-language questions match.
    document_texts = []
    document_indices = []

    for index, doc in enumerate(documents):
        document_texts.append(
            f"{doc['title']}. {doc['question']} {doc['answer']}"
        )
        document_indices.append(index)

        document_texts.append(doc["question"])
        document_indices.append(index)

    document_vectors = model.encode(
        document_texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    question_vector = model.encode(
        [question.strip()],
        normalize_embeddings=True,
        convert_to_numpy=True,
    )[0]

    
    # Compare the question with every FAQ representation.
    # Map the best match back to its original FAQ document.
    scores = document_vectors @ question_vector
    best_match_index = int(scores.argmax())
    best_score = float(scores[best_match_index])
    best_index = document_indices[best_match_index]
    best_document = documents[best_index]

    if best_score < threshold:
        return {
            "found": False,
            "answer": FALLBACK_ANSWER,
            "source": None,
            "score": round(best_score, 4),
            "kb_version": kb_version,
        }

    return {
        "found": True,
        "answer": best_document["answer"],
        "source": best_document["source"],
        "document_id": best_document["id"],
        "score": round(best_score, 4),
        "kb_version": kb_version,
    }


if __name__ == "__main__":
    question = input("Ask a finance question: ")
    result = search_knowledge_base(question)

    print("\nAnswer:", result["answer"])
    print("Source:", result["source"] or "No matching source")
    print("Relevance score:", result["score"])
    print("Knowledge Base version:", result["kb_version"])
