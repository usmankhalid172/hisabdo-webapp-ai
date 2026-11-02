"""
Blog & News Pipeline — Grounded Generation & Citations
======================================================
Aligned prompts, citation handling, conflict resolution, and 6 fallback
mechanisms for the Blog & News domain.

Consumes the retrieval pipeline (src/retrieval.py) and produces grounded
LLM responses with inline citations [1][2][3], a Sources block, conflict
disclosures, and fallback handling.

Usage:
    from src.grounded_generation import generate_grounded_response
    result = generate_grounded_response("how much does custom software cost")
    print(result["response"])
"""

import re
from datetime import datetime, timedelta

from .retrieval import Retriever, DEFAULT_TOP_K
from .utils import (
    is_out_of_domain, is_stale, is_valid_blog_url, BLOG_URL_PATTERN,
)

# ============================================================
# CONFIG
# ============================================================
STALE_ARTICLE_MONTHS = 18
MULTI_SOURCE_SCORE_GAP = 0.05
MULTI_SOURCE_MIN_SCORE = 0.20

# ============================================================
# SYSTEM PROMPT
# ============================================================
SYSTEM_PROMPT = """You are the XICTEK Systems website assistant for the Blog & News section.
Your job is to answer user questions using ONLY the blog articles provided
in the context. You must follow these rules:

GROUNDING RULES
1. Every factual claim in your answer MUST be supported by one of the
   provided source articles. If no source supports a claim, do not make
   the claim.
2. If the provided sources do not contain enough information to answer
   the question, say so explicitly and offer to direct the user to
   contact XICTEK Systems. Do not fabricate, infer, or generalize
   beyond what the sources state.
3. Do not use outside knowledge. Do not use training-data knowledge of
   XICTEK Systems, its products, or its services. Only the provided
   source articles are valid grounding.

CITATION RULES
4. Cite sources using inline numbered markers: [1], [2], [3]. Place the
   marker immediately after the claim it supports, before the period.
5. At the end of your response, include a "Sources:" section listing
   each cited article in the format:
       [n] Article Title — https://www.xicteksystems.com/blog/<slug>
6. Only cite an article if you actually used information from it. Do not
   pad the Sources list with articles you did not draw on.
7. If you quote a sentence or phrase verbatim from a source, wrap it in
   quotation marks and cite the source. Do not pass off source text as
   your own.

CONFLICT RULES
8. If two provided sources give contradictory information, do not pick
   one silently. Lead with the stronger source, then add a "Note:"
   line disclosing the conflict and citing the second source.
9. If the contradiction is material (different pricing, different
   recommendations, different technical claims), prefer disclosure over
   synthesis — let the user see both sources and decide.

SCOPE RULES
10. Only cite URLs on the www.xicteksystems.com domain, and only URLs
    on the /blog/ path. Never cite /services, /contact, /about, or
    external domains (hisabdo.app, LinkedIn, etc.) as Blog sources.
11. If the user's question is about pricing, services, or contact
    information rather than blog content, deflect to the appropriate
    page (/services, /contact) instead of guessing from blog articles.

FALLBACK RULES
12. If no source articles are provided (empty context), respond with:
    "I don't have a blog article that addresses that. For specific
    questions, please contact XICTEK Systems at xicteksystems@gmail.com
    or visit /contact."
13. If all provided sources have similarity scores below the threshold,
    treat the context as empty (rule 12).
14. If the user's question is ambiguous, ask one clarifying question
    rather than guessing. Do not retrieve and answer a different
    question than the one asked.

TONE
15. Professional, restrained, no hype. No exclamation marks. No
    marketing language. The user is evaluating XICTEK; honest answers
    build more trust than overclaimed ones."""


# ============================================================
# PROMPT BUILDING
# ============================================================
def build_user_prompt(query, retrieved_articles, k=DEFAULT_TOP_K, threshold=0.15):
    """Assemble the user prompt with retrieved articles as context."""
    lines = []
    lines.append(f"USER QUESTION:")
    lines.append(query)
    lines.append("")
    lines.append(f"RETRIEVED BLOG ARTICLES (top {k}, similarity threshold {threshold:.2f}):")
    lines.append("")
    for i, art in enumerate(retrieved_articles, 1):
        pub = art['publish_date'].strftime("%B %d, %Y") if art.get('publish_date') else "unknown"
        lines.append(f"--- ARTICLE [{i}] ---")
        lines.append(f"Title: {art['title']}")
        lines.append(f"URL: https://www.xicteksystems.com/blog/{art['slug']}")
        lines.append(f"Category: {art['category']}")
        lines.append(f"Published: {pub}")
        lines.append(f"Similarity score: {art['score']:.4f}")
        lines.append("Section excerpt:")
        body = art['body'][:1500]
        if len(art['body']) > 1500:
            body += " [...]"
        lines.append(body)
        lines.append("")
    lines.append("INSTRUCTIONS:")
    lines.append("Answer the user's question using ONLY the articles above. Follow the")
    lines.append("grounding, citation, conflict, scope, and fallback rules in your system")
    lines.append("prompt. If the articles do not support an answer, say so. Do not")
    lines.append("fabricate. Do not use outside knowledge.")
    return "\n".join(lines)


# ============================================================
# CITATION FORMATTING
# ============================================================
def format_citation(article, index, section=None):
    """Format a single Sources entry."""
    url = f"https://www.xicteksystems.com/blog/{article['slug']}"
    if section:
        return f"[{index}] {article['title']} — § \"{section}\" — {url}"
    return f"[{index}] {article['title']} — {url}"


# ============================================================
# SCOPE VIOLATION CHECK (extended for dangerous URI schemes)
# ============================================================
# Legitimate fallback deflection URLs — allowed in fallback responses
LEGITIMATE_FALLBACK_URLS = frozenset({
    "https://www.xicteksystems.com/contact",
    "https://www.xicteksystems.com/services",
    "https://www.xicteksystems.com/about",
    "https://www.xicteksystems.com/careers",
})

# Dangerous URI schemes that should never appear in a response
DANGEROUS_URI_PATTERN = re.compile(
    r'(javascript:|file:///|data:|vbscript:|blob:)', re.IGNORECASE
)

def check_scope_violations(response):
    """Strip any URL that doesn't match the blog URL allowlist.
    Also strips dangerous URI schemes (javascript:, file:, data:, etc.).
    Legitimate fallback deflection URLs (/contact, /services) are allowed.
    Returns (cleaned_response, list_of_blocked_urls)."""
    blocked = []
    cleaned = response

    # 1. Strip dangerous URI schemes first (javascript:, file:, data:, etc.)
    for m in DANGEROUS_URI_PATTERN.finditer(response):
        # Find the full URI to block (scheme + non-whitespace chars)
        start = m.start()
        end = start
        while end < len(response) and response[end] not in ' \t\n\r)"]':
            end += 1
        dangerous_uri = response[start:end]
        blocked.append(dangerous_uri)
        cleaned = cleaned.replace(dangerous_uri, '')

    # 2. Strip non-blog HTTP(S) URLs (except legitimate fallback URLs)
    url_pattern = re.compile(r'https?://[^\s\)\]]+')
    urls_in_response = url_pattern.findall(cleaned)
    for url in urls_in_response:
        clean_url = url.rstrip('.,;:')
        if not is_valid_blog_url(clean_url) and clean_url not in LEGITIMATE_FALLBACK_URLS:
            blocked.append(clean_url)
            cleaned = cleaned.replace(url, '').replace(clean_url, '')

    return cleaned, blocked


# ============================================================
# INPUT SANITIZER (prompt-injection defense)
# ============================================================
# Known prompt-injection patterns to strip from user queries
INJECTION_PATTERNS = [
    re.compile(r'ignore\s+(?:all\s+)?previous\s+instructions', re.IGNORECASE),
    re.compile(r'forget\s+(?:all\s+)?(?:previous\s+)?(?:rules|instructions)', re.IGNORECASE),
    re.compile(r'\[SYSTEM\]', re.IGNORECASE),
    re.compile(r'\[IMPORTANT\s+SYSTEM\s+UPDATE\]', re.IGNORECASE),
    re.compile(r'you\s+are\s+now\s+a\s+different\s+assistant', re.IGNORECASE),
    re.compile(r'override\s+(?:your\s+)?(?:scope|grounding|citation)\s+rules', re.IGNORECASE),
    re.compile(r'i\s+am\s+the\s+admin', re.IGNORECASE),
    re.compile(r'remember\s+for\s+next\s+time', re.IGNORECASE),
]

# Base64-looking strings (suspicious — may be encoded injection)
BASE64_PATTERN = re.compile(r'\b[A-Za-z0-9+/]{40,}={0,2}\b')

def sanitize_user_query(query):
    """Strip known prompt-injection patterns from user queries.
    Returns the sanitized query. Does NOT decode base64 (too risky to execute)."""
    sanitized = query
    for pattern in INJECTION_PATTERNS:
        sanitized = pattern.sub('[REDACTED]', sanitized)
    # Flag base64-looking strings by replacing them (don't decode — could be malicious)
    sanitized = BASE64_PATTERN.sub('[REDACTED_BASE64]', sanitized)
    return sanitized


# ============================================================
# OUTPUT PII FILTER (system-prompt leak defense)
# ============================================================
# Markers that should NEVER appear in a user-facing response
SYSTEM_PROMPT_MARKERS = [
    "GROUNDING RULES", "CITATION RULES", "CONFLICT RULES",
    "SCOPE RULES", "FALLBACK RULES", "SYSTEM_PROMPT",
    "You are the XICTEK Systems website assistant",
    "Do not use outside knowledge",
]

CONFIG_MARKERS = [
    "threshold = 0.15", "top_k = 3", "alpha = 0.5",
    "Hybrid α", "MiniLM-L6-v2", "TF-IDF vectorizer",
]

def filter_pii_from_response(response):
    """Redact system prompt markers and config values from the LLM response.
    Returns (filtered_response, list_of_redacted_markers)."""
    filtered = response
    redacted = []
    for marker in SYSTEM_PROMPT_MARKERS:
        if marker.lower() in filtered.lower():
            redacted.append(marker)
            # Case-insensitive replace
            filtered = re.sub(re.escape(marker), '[REDACTED]', filtered, flags=re.IGNORECASE)
    for marker in CONFIG_MARKERS:
        if marker.lower() in filtered.lower():
            redacted.append(marker)
            filtered = re.sub(re.escape(marker), '[REDACTED]', filtered, flags=re.IGNORECASE)
    return filtered, redacted


# ============================================================
# CONFLICT DETECTION
# ============================================================
def detect_conflicts(response, cited_articles):
    """Heuristic conflict detection. Returns list of conflict dicts."""
    conflicts = []
    note_pattern = re.compile(r'Note:\s.*?\[(\d)\].*?\[(\d)\]', re.IGNORECASE | re.DOTALL)
    for m in note_pattern.finditer(response):
        idx1, idx2 = int(m.group(1)), int(m.group(2))
        conflicts.append({
            'type': 'llm_disclosed',
            'articles': [idx1, idx2],
            'snippet': m.group(0)[:200],
        })
    num_pattern = re.compile(r'(\d+(?:[.-]\d+)?\s*(?:weeks?|months?|days?|hours?|\$|%\s*)?)\s*\[(\d)\]\s*\[(\d)\]')
    for m in num_pattern.finditer(response):
        num, idx1, idx2 = m.group(1), int(m.group(2)), int(m.group(3))
        conflicts.append({
            'type': 'numerical_mismatch',
            'articles': [idx1, idx2],
            'snippet': f"Number '{num}' attributed to two sources",
        })
    return conflicts


# ============================================================
# MULTI-SOURCE DETECTION
# ============================================================
def is_multi_source(retrieved, gap=MULTI_SOURCE_SCORE_GAP, min_score=MULTI_SOURCE_MIN_SCORE):
    """Check if 2+ articles are within `gap` of each other and above `min_score`."""
    if len(retrieved) < 2:
        return False
    scores = [s for _, s in retrieved] if isinstance(retrieved[0], tuple) else \
             [a['score'] for a in retrieved]
    return (scores[0] >= min_score and scores[1] >= min_score
            and (scores[0] - scores[1]) <= gap)


# ============================================================
# FALLBACK HELPERS
# ============================================================
def append_stale_note(response, article):
    """Append a recency note for stale articles."""
    if not article.get('publish_date'):
        return response
    pub_str = article['publish_date'].strftime("%B %Y")
    note = (
        f"\n\nNote: This article was published in {pub_str}. Some specifics "
        "(technology versions, pricing) may have changed since then — confirm "
        "with XICTEK Systems for current information."
    )
    return response + note


# ============================================================
# SIMULATED LLM RESPONSE (for testing without a real LLM)
# ============================================================
def _simulate_llm_response(query, retrieved_articles):
    """Generate a simulated grounded response for testing."""
    if not retrieved_articles:
        return "I don't have a blog article that addresses that."
    top = retrieved_articles[0]
    url = f"https://www.xicteksystems.com/blog/{top['slug']}"
    response = (
        f"Based on the {top['title']} article [1], "
        f"the key considerations for your question are covered in the article's "
        f"discussion of this topic. The article emphasizes starting with a clear "
        f"business outcome before making technical decisions [1]."
    )
    if len(retrieved_articles) >= 2 and is_multi_source(retrieved_articles):
        second = retrieved_articles[1]
        response += (
            f"\n\nA related perspective appears in {second['title']} [2], which "
            f"covers the same topic from a different angle."
        )
    response += "\n\n**Sources:**\n"
    response += f"[1] {top['title']} — {url}\n"
    if len(retrieved_articles) >= 2 and is_multi_source(retrieved_articles):
        second_url = f"https://www.xicteksystems.com/blog/{retrieved_articles[1]['slug']}"
        response += f"[2] {retrieved_articles[1]['title']} — {second_url}\n"
    return response


# ============================================================
# MAIN ENTRY POINT
# ============================================================
def generate_grounded_response(query, llm_client=None, top_k=DEFAULT_TOP_K,
                                retriever=None):
    """End-to-end grounded generation.

    Args:
        query: user's question string
        llm_client: callable(system_prompt, user_prompt) -> response string.
                    If None, uses simulated response for testing.
        top_k: number of articles to retrieve (default 3)
        retriever: optional Retriever instance (default: create one)

    Returns:
        dict with: response, retrieved_articles, fallbacks_triggered,
                   scope_violations, conflicts_detected, logs
    """
    logs = []
    fallbacks_triggered = []

    # Step 1: out-of-domain check (Fallback 5.2)
    ood_keywords = is_out_of_domain(query)
    if ood_keywords:
        fallbacks_triggered.append("5.2_OUT_OF_DOMAIN")
        logs.append({"event": "FALLBACK_OUT_OF_DOMAIN", "query": query,
                     "matched_keywords": ood_keywords})
        return {
            "response": (
                "That question is best answered on our "
                "[Services](https://www.xicteksystems.com/services) or "
                "[Contact](https://www.xicteksystems.com/contact) page rather than in the blog. "
                "I'd suggest starting there — or if you'd like, I can answer a related "
                "question from our blog articles."
            ),
            "retrieved_articles": [],
            "fallbacks_triggered": fallbacks_triggered,
            "scope_violations": [],
            "conflicts_detected": [],
            "logs": logs,
        }

    # Step 2: retrieve (with sanitized query)
    if retriever is None:
        retriever = Retriever()
    sanitized_query = sanitize_user_query(query)
    if sanitized_query != query:
        logs.append({"event": "INPUT_SANITIZED", "query": query,
                     "sanitized_query": sanitized_query})
    retrieved_articles = retriever.search_with_articles(sanitized_query, top_k=top_k)

    # Step 3: no-source fallback (5.1)
    if not retrieved_articles:
        fallbacks_triggered.append("5.1_NO_SOURCE")
        logs.append({"event": "FALLBACK_NO_SOURCE", "query": query, "top_score": 0.0})
        return {
            "response": (
                "I don't have a blog article that addresses that. For specific questions, "
                "please contact XICTEK Systems at xicteksystems@gmail.com or visit "
                "[/contact](https://www.xicteksystems.com/contact)."
            ),
            "retrieved_articles": [],
            "fallbacks_triggered": fallbacks_triggered,
            "scope_violations": [],
            "conflicts_detected": [],
            "logs": logs,
        }

    # Log multi-source case (5.5)
    if is_multi_source(retrieved_articles):
        logs.append({
            "event": "FALLBACK_MULTIPLE_EQUAL", "query": query,
            "slugs": [retrieved_articles[0]['slug'], retrieved_articles[1]['slug']],
            "scores": [retrieved_articles[0]['score'], retrieved_articles[1]['score']],
        })
        fallbacks_triggered.append("5.5_MULTIPLE_EQUAL")

    # Step 4: build prompt
    user_prompt = build_user_prompt(query, retrieved_articles, k=top_k)

    # Step 5: call LLM (or simulate)
    if llm_client is None:
        response = _simulate_llm_response(query, retrieved_articles)
    else:
        response = llm_client(SYSTEM_PROMPT, user_prompt)

    # Step 6: post-process
    # 6a. Scope violations (5.3) — strips non-blog URLs + dangerous URI schemes
    response, blocked_urls = check_scope_violations(response)
    if blocked_urls:
        fallbacks_triggered.append("5.3_SCOPE_VIOLATION")
        for url in blocked_urls:
            logs.append({"event": "FALLBACK_SCOPE_VIOLATION", "query": query, "blocked_url": url})

    # 6b. PII filter — redact system prompt markers and config values
    response, redacted_markers = filter_pii_from_response(response)
    if redacted_markers:
        fallbacks_triggered.append("PII_REDACTED")
        for marker in redacted_markers:
            logs.append({"event": "PII_REDACTED", "query": query, "redacted_marker": marker})

    # 6c. Conflict detection (§4)
    conflicts = detect_conflicts(response, retrieved_articles)
    for c in conflicts:
        logs.append({"event": "CONFLICT_DISCLOSED", "query": query,
                     "conflict_type": c['type'], "articles": c['articles']})

    # 6c. Stale article note (5.6)
    cited_indices = set(int(m.group(1)) for m in re.finditer(r'\[(\d)\]', response))
    if cited_indices:
        top_cited_idx = min(cited_indices)
        if top_cited_idx <= len(retrieved_articles):
            top_article = retrieved_articles[top_cited_idx - 1]
            if is_stale(top_article):
                fallbacks_triggered.append("5.6_STALE_ARTICLE")
                logs.append({
                    "event": "FALLBACK_STALE_ARTICLE", "query": query,
                    "slug": top_article['slug'],
                    "publish_date": top_article['publish_date'].strftime("%Y-%m-%d") if top_article['publish_date'] else None,
                })
                response = append_stale_note(response, top_article)

    return {
        "response": response,
        "retrieved_articles": retrieved_articles,
        "fallbacks_triggered": fallbacks_triggered,
        "scope_violations": blocked_urls,
        "conflicts_detected": conflicts,
        "logs": logs,
    }
