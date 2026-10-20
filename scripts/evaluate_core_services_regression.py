"""Run an offline Core Services retrieval/link and formatting regression suite.

Run from the repository root:

    python scripts/evaluate_core_services_regression.py

This uses the checked-in index and the fitted TF-IDF vectorizer. It makes no
LLM or network calls. It checks retrieval, source-link accuracy and formatting
fixtures, but does not claim to test live generated answers.
"""
from __future__ import annotations

import ast
import json
import pickle
import re
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.xictek_website_assistant.formatting import format_core_services_output
from src.xictek_website_assistant.service_queries import is_core_services_query

INDEX_DIR = REPO_ROOT / "src" / "xictek_website_assistant" / "data" / "index"
TOP_K = 4
RELEVANCE_THRESHOLD = 0.22
MMR_LAMBDA = 0.5


@dataclass(frozen=True)
class QueryCase:
    name: str
    query: str
    expected_path: str


CASES = (
    QueryCase("custom scope", "What custom software services do you offer?", "/services/custom-software-development"),
    QueryCase("workflow discovery", "How do you map workflows before building software?", "/services/custom-software-development"),
    QueryCase("product foundations", "What foundations support future product development?", "/services/custom-software-development"),
    QueryCase("small software launch", "Can a software project begin with a small release?", "/services/custom-software-development"),
    QueryCase("custom software punctuation", "Custom software: can you build APIs and business systems?", "/services/custom-software-development"),
    QueryCase("web application types", "What types of web applications do you build?", "/services/web-development"),
    QueryCase("web technology stack", "Which technologies are used in web development?", "/services/web-development"),
    QueryCase("web app improvement", "Can you improve an existing web app's performance and usability?", "/services/web-development"),
    QueryCase("web SEO and accessibility", "Does web development include SEO and accessibility?", "/services/web-development"),
    QueryCase("website product query", "Which technology stack do you use for web apps?", "/services/web-development"),
    QueryCase("mobile cross-platform", "Which framework supports mobile apps across iOS and Android?", "/services/mobile-app-development"),
    QueryCase("mobile offline", "Can your mobile apps work offline?", "/services/mobile-app-development"),
    QueryCase("mobile notifications", "How are notifications integrated into mobile apps?", "/services/mobile-app-development"),
    QueryCase("mobile integrations", "Can mobile apps integrate payments or business systems?", "/services/mobile-app-development"),
    QueryCase("mobile user experience", "How do you make mobile apps feel native on each platform?", "/services/mobile-app-development"),
    QueryCase("cloud platforms", "Which cloud platforms do you work with?", "/services/cloud-solutions"),
    QueryCase("cloud migration", "Could you migrate an existing application to Azure?", "/services/cloud-solutions"),
    QueryCase("cloud deployments", "What supports repeatable cloud deployment?", "/services/cloud-solutions"),
    QueryCase("cloud reliability", "How do you improve cloud reliability and cost visibility?", "/services/cloud-solutions"),
    QueryCase("cloud short query", "Azure hosting and cloud architecture?", "/services/cloud-solutions"),
    QueryCase("AI integration", "Which AI integration and automation services do you offer?", "/services/ai-solutions"),
    QueryCase("AI development process", "How do you test AI features before production?", "/services/ai-solutions"),
    QueryCase("AI for existing apps", "Can you add AI features to an existing app?", "/services/ai-solutions"),
    QueryCase("AI safeguards", "What safeguards are used in production AI?", "/services/ai-solutions"),
    QueryCase("AI short query", "AI chatbot and document processing?", "/services/ai-solutions"),
    QueryCase("ERP modules", "What ERP workflows and modules can you build?", "/services/erp-development"),
    QueryCase("ERP records", "Can ERP cover inventory and customer records?", "/services/erp-development"),
    QueryCase("ERP rollout", "Can an ERP project start with one department?", "/services/erp-development"),
    QueryCase("ERP customization", "What does ERP customization involve?", "/services/erp-development"),
    QueryCase("SaaS tenancy", "What does multi-tenancy mean for a SaaS product?", "/services/saas-development"),
    QueryCase("SaaS billing", "How are subscriptions and billing handled?", "/services/saas-development"),
    QueryCase("SaaS roles", "Does SaaS include role-based access?", "/services/saas-development"),
    QueryCase("SaaS analytics", "What analytics can SaaS provide?", "/services/saas-development"),
    QueryCase("SaaS MVP", "Can you build an MVP for a SaaS product?", "/services/saas-development"),
)


def _load_query_expansion() -> tuple[dict[str, str], float]:
    """Read the production expansion constants without importing app settings."""
    source = REPO_ROOT / "src" / "xictek_website_assistant" / "embeddings.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    values: dict[str, object] = {}
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "_SYNONYMS":
                values[node.target.id] = ast.literal_eval(node.value)
        elif isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "_EXPANSION_WEIGHT"
            for target in node.targets
        ):
            values["_EXPANSION_WEIGHT"] = ast.literal_eval(node.value)
    return values["_SYNONYMS"], float(values["_EXPANSION_WEIGHT"])


def _load_thresholds() -> tuple[int, float]:
    """Read current default top-k and threshold from config.py."""
    source = (REPO_ROOT / "src" / "xictek_website_assistant" / "config.py").read_text(encoding="utf-8")
    top_k_match = re.search(r"core_services_top_k:\s*int\s*=\s*Field\(default=(\d+)", source)
    threshold_match = re.search(
        r"core_services_relevance_threshold:\s*float\s*=\s*Field\(default=([0-9.]+)", source
    )
    if not top_k_match or not threshold_match:
        raise RuntimeError("Could not read Core Services top-k/threshold defaults from config.py")
    return int(top_k_match.group(1)), float(threshold_match.group(1))


def _query_vector(query: str, vectorizer, synonyms: dict[str, str], expansion_weight: float) -> np.ndarray:
    vector = vectorizer.transform([query]).toarray()[0].astype(np.float32)
    expansion_terms: list[str] = []
    for token in re.findall(r"[a-z]+", query.lower()):
        expansion_terms.extend(synonyms.get(token, "").split())
    expansion = " ".join(dict.fromkeys(expansion_terms))
    if expansion:
        extra = vectorizer.transform([expansion]).toarray()[0].astype(np.float32)
        vector += expansion_weight * extra
        norm = float(np.linalg.norm(vector))
        if norm:
            vector /= norm
    return vector


def _retrieve(
    query: str,
    chunks: list[dict],
    vectors: np.ndarray,
    vectorizer,
    synonyms: dict[str, str],
    expansion_weight: float,
    top_k: int,
    threshold: float,
) -> list[tuple[dict, float]]:
    query_vector = _query_vector(query, vectorizer, synonyms, expansion_weight)
    scores = vectors @ query_vector
    candidates = np.array(
        [
            i for i, chunk in enumerate(chunks)
            if (path := urlsplit(chunk.get("url") or "").path.rstrip("/").casefold()) == "/services"
            or path.startswith("/services/")
        ],
        dtype=int,
    )
    candidates = candidates[scores[candidates] >= threshold]
    candidates = candidates[np.argsort(-scores[candidates], kind="stable")]
    candidates = candidates[: min(len(candidates), max(top_k * 50, 300))]

    selected: list[int] = []
    remaining = list(candidates)
    while remaining and len(selected) < top_k:
        if not selected:
            best = remaining[0]
        else:
            selected_vectors = vectors[selected]
            best = max(
                remaining,
                key=lambda i: MMR_LAMBDA * float(scores[i])
                - (1 - MMR_LAMBDA) * float(np.max(selected_vectors @ vectors[i])),
            )
        selected.append(best)
        remaining.remove(best)
    return [(chunks[i], float(scores[i])) for i in selected]


def _check_formatting() -> list[str]:
    failures: list[str] = []
    cases = (
        (
            "compound semicolon list",
            "LLM and OpenAI integrations; AI assistants and chatbots; document processing and extraction.",
            ["LLM and OpenAI integrations", "AI assistants and chatbots", "document processing and extraction"],
        ),
        (
            "Next.js punctuation list",
            "React, Next.js, TypeScript, PostgreSQL, and cloud services.",
            ["React", "Next.js", "TypeScript", "PostgreSQL", "cloud services"],
        ),
    )
    for label, source, expected in cases:
        actual = [
            match.group(1).strip()
            for line in format_core_services_output(source).splitlines()
            if (match := re.match(r"^\s*-\s+(.+?)\s*$", line))
        ]
        if actual != expected:
            failures.append(f"formatting/{label}: expected {expected!r}, got {actual!r}")

    for label, source in (
        ("single item", "XICTEK offers Flutter."),
        ("ordinary prose", "XICTEK supports teams throughout delivery."),
    ):
        if format_core_services_output(source) != source:
            failures.append(f"formatting/{label}: prose was changed unexpectedly")
    return failures


def main() -> int:
    chunks_path = INDEX_DIR / "chunks.json"
    vectors_path = INDEX_DIR / "embeddings.npy"
    vectorizer_path = INDEX_DIR / "tfidf_vectorizer.pkl"
    missing = [str(path) for path in (chunks_path, vectors_path, vectorizer_path) if not path.exists()]
    if missing:
        print("FAIL  missing persisted index files:")
        for path in missing:
            print(f"      - {path}")
        return 2

    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    vectors = np.load(vectors_path)
    with vectorizer_path.open("rb") as file:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            vectorizer = pickle.load(file)
    if len(chunks) != vectors.shape[0]:
        print(f"FAIL  index mismatch: {len(chunks)} chunks vs {vectors.shape[0]} vectors")
        return 2

    synonyms, expansion_weight = _load_query_expansion()
    top_k, threshold = _load_thresholds()
    failures = 0
    for case in CASES:
        reasons: list[str] = []
        if not is_core_services_query(case.query):
            reasons.append("query did not route to Core Services retrieval")
        retrieved = _retrieve(
            case.query, chunks, vectors, vectorizer, synonyms, expansion_weight, top_k, threshold
        )
        result_urls = [chunk.get("url") or "" for chunk, _ in retrieved]
        if not any(urlsplit(url).path.rstrip("/").casefold().startswith(case.expected_path) for url in result_urls):
            best = max(
                (
                    float(vectors[i] @ _query_vector(case.query, vectorizer, synonyms, expansion_weight))
                    for i, chunk in enumerate(chunks)
                    if urlsplit(chunk.get("url") or "").path.rstrip("/").casefold().startswith(case.expected_path)
                ),
                default=0.0,
            )
            reasons.append(
                f"expected source {case.expected_path} absent from top {top_k}; best expected-page score {best:.4f} at cutoff {threshold:.2f}"
            )
        if any(
            urlsplit(url).netloc.casefold().removeprefix("www.") != "xicteksystems.com"
            or not (
                (path := urlsplit(url).path.rstrip("/").casefold()) == "/services"
                or path.startswith("/services/")
            )
            for url in result_urls
        ):
            reasons.append("retrieval returned a source outside xicteksystems.com/services")
        if reasons:
            failures += 1
            print(f"FAIL  {case.name}: " + "; ".join(reasons))
        else:
            source_urls = ", ".join(dict.fromkeys(result_urls))
            print(f"PASS  {case.name}: {source_urls}")

    format_failures = _check_formatting()
    for reason in format_failures:
        failures += 1
        print(f"FAIL  {reason}")
    formatting_checks = 4
    passed = len(CASES) + formatting_checks - failures
    print(
        f"\nResult: {passed}/{len(CASES) + formatting_checks} checks passed; "
        f"{failures} failed. Retrieval: {len(CASES)} queries, top-k={top_k}, "
        f"cosine cutoff={threshold:.2f}. Formatting: {formatting_checks} checks."
    )
    if caught:
        print("NOTE  Pickle load emitted a compatibility warning; use the pinned requirements environment for final score calibration.")
    print("Scope: saved-index retrieval and deterministic formatting fixtures; no live LLM or network request.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
