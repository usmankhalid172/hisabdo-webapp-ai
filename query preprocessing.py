"""
Query preprocessing utilities for the HisabDo / XICTEK website assistant.

Purpose
-------
Standardize product-related user queries before they are sent to the embedding
model and vector store. This can make differently formatted questions more
consistent, while leaving the vector store's ranking and filtering behavior
unchanged.

Integration
-----------
Import `preprocess_product_query` in the chat service and call it immediately
before generating the query embedding. Use the returned string for retrieval.

Example:
    from src.xictek_website_assistant.query_preprocessing import (
        preprocess_product_query,
    )

    cleaned_query = preprocess_product_query(user_message)
    query_vector = embedding_service.embed_query(cleaned_query)
    results = vector_store.query(query_vector, top_k=5)

This module does not call an embedding provider or the vector store itself.
This module only implements test cases. 
"""

import re
from typing import Mapping


# Map common user wording to the terminology used in product documentation.
# Keep this dictionary small and specific to avoid changing the user's meaning.
# Add or adjust entries to match the verified HisabDo Knowledge Base terminology.
DEFAULT_KEYWORD_MAP: Mapping[str, str] = {
    # Financial concepts: use terminology present in the supplied knowledge base.
    "spending": "expense",
    "spendings": "expense",
    "cost": "expense",
    "costs": "expense",
    "earning": "revenue",
    "earnings": "revenue",
    "income": "revenue",
    "sales": "revenue",

    # Customer balances and payments.
    "balances": "balance",
    "owed": "outstanding",
    "unpaid": "outstanding",
    "payments": "payment",

    # Expense categorization.
    "categories": "category",
}


def _normalize_possessives(query: str) -> str:
    """
    Handle common English possessives before punctuation is removed.

    Examples:
        "HisabDo's features" -> "HisabDo features"
        "users' reports"    -> "users reports"

    This avoids accidentally turning "HisabDo's" into "hisabdos".
    The transformation is intentionally simple and intended for product
    queries in English, not as a full natural-language parser.
    """
    # Remove apostrophe + s at a word boundary: "HisabDo's" -> "HisabDo".
    query = re.sub(r"(?i)(\b[\w-]+)'s\b", r"\1", query)

    # Remove a trailing apostrophe from plural possessives: "users'" -> "users".
    query = re.sub(r"(?<=\w)'(?=\s|$)", "", query)

    return query


def preprocess_product_query(
    query: str,
    keyword_map: Mapping[str, str] | None = None,
) -> str:
    """
    Clean and normalize a user query before vector-store retrieval.

    Processing steps:
      1. Validate the input is a string.
      2. Trim leading/trailing whitespace.
      3. Normalize common possessives before stripping punctuation.
      4. Convert text to lowercase.
      5. Replace punctuation with spaces, preserving letters, numbers,
         underscores, and whitespace.
      6. Normalize selected whole-word keywords.
      7. Collapse repeated whitespace.

    Args:
        query: The original user message.
        keyword_map: Optional mapping of words to their canonical terms.
            If omitted, DEFAULT_KEYWORD_MAP is used. Keys and values are
            normalized to lowercase for consistent matching.

    Returns:
        A cleaned query string. Empty or whitespace-only input returns "".

    Raises:
        TypeError: If `query` is not a string.
    """
    # Reject unexpected input types instead of silently converting objects.
    if not isinstance(query, str):
        raise TypeError("query must be a string")

    # Trim whitespace and return early for empty input.
    query = query.strip()
    if not query:
        return ""

    # Preserve the intended product name in possessive phrases before
    # removing punctuation such as apostrophes.
    query = _normalize_possessives(query)

    # Standardize capitalization so matching is case-insensitive.
    query = query.lower()

    # Replace punctuation with spaces rather than deleting it directly.
    # For example, "income/expenses" becomes "income expenses" instead of
    # merging words into "incomeexpenses".
    query = re.sub(r"[^\w\s]", " ", query, flags=re.UNICODE)

    # Split into individual tokens after punctuation cleanup.
    words = query.split()

    # Use the supplied mapping if present; otherwise use the defaults.
    selected_map = DEFAULT_KEYWORD_MAP if keyword_map is None else keyword_map

    # Normalize map keys and values to lowercase and single-token strings.
    # Only whole-word tokens are replaced, so "cost" will not alter
    # unrelated words that merely contain those letters.
    normalized_map = {
        str(source).strip().lower(): str(target).strip().lower()
        for source, target in selected_map.items()
        if str(source).strip() and str(target).strip()
    }

    # Replace known synonyms with the terminology used by the Knowledge Base.
    words = [normalized_map.get(word, word) for word in words]

    # Joining with one space collapses repeated spaces, tabs, and newlines.
    return " ".join(words)


if __name__ == "__main__":
    # Simple manual checks that can be run with:
    # python query_preprocessing.py
    examples = [
        "WHAT IS HISABDO?",
        "Tell me about HisabDo's FEATURES!!!",
        "Show my spending.",
        "How do I view my earnings?",
        "Give me summaries   of my business.",
        "   ",
    ]

    for original in examples:
        print(f"Original: {original!r}")
        print(f"Cleaned:  {preprocess_product_query(original)!r}")
        print()
