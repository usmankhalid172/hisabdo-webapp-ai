import csv
import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[1]
STAGING = ROOT / "data" / "department3_ingestion"
INPUT = ROOT / "docs" / "evaluation" / "retrieval_results_v1.0.csv"
OUTPUT = ROOT / "docs" / "evaluation" / "department3_staged_retrieval_results_v1.0.csv"
REPORT = ROOT / "docs" / "evaluation" / "department3_staged_retrieval_report_v1.0.md"

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
THRESHOLD = 0.40
TOP_K = 3
DIMENSION = 384


def main():
    chunks = json.loads(
        (STAGING / "chunks.json").read_text(encoding="utf-8")
    )
    vectors = np.load(STAGING / "embeddings.npy")

    if vectors.shape != (len(chunks), DIMENSION):
        raise ValueError(
            f"Invalid vector shape: {vectors.shape}"
        )
    if not np.isfinite(vectors).all():
        raise ValueError("Embedding matrix contains non-finite values")

    norms = np.linalg.norm(vectors, axis=1)
    if len(vectors) and not np.allclose(norms, 1.0, atol=1e-4):
        raise ValueError("Embedding vectors are not L2-normalized")

    with INPUT.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    if len(rows) != 60:
        raise ValueError(f"Expected 60 evaluation questions, found {len(rows)}")

    model = SentenceTransformer(
        MODEL_ID, revision=REVISION, device="cpu"
    )
    queries = [row["Question"] for row in rows]
    query_vectors = model.encode(
        queries,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=True,
    ).astype(np.float32)

    staged_ids = {chunk["document_id"] for chunk in chunks}
    results = []

    for row, query_vector in zip(rows, query_vectors):
        scores = vectors @ query_vector

        # Keep only the best-scoring chunk for each source document.
        best_by_document = {}
        for index, score in enumerate(scores):
            chunk = chunks[index]
            doc_id = chunk["document_id"]
            if doc_id not in best_by_document or score > best_by_document[doc_id][0]:
                best_by_document[doc_id] = (float(score), chunk)

        ranked = sorted(
            best_by_document.items(),
            key=lambda item: item[1][0],
            reverse=True,
        )
        selected = [
            (doc_id, score, chunk)
            for doc_id, (score, chunk) in ranked
            if score >= THRESHOLD
        ][:TOP_K]

        retrieved_ids = [item[0] for item in selected]
        expected_ids = [
            value.strip()
            for value in row["Expected_Source_IDs"].split(";")
            if value.strip()
        ]
        verified = row["Source_Status"].strip().lower() == "verified"

        if verified and expected_ids:
            available_expected = set(expected_ids) & staged_ids
            if not available_expected:
                outcome = "OUT_OF_SCOPE"
            elif set(retrieved_ids) & set(expected_ids):
                outcome = "MATCH"
            else:
                outcome = "MISS"
        elif retrieved_ids:
            outcome = "REVIEW"
        else:
            outcome = "SAFE_ABSTENTION"

        results.append({
            "Test_ID": row["Test_ID"],
            "Question": row["Question"],
            "Expected_Source_IDs": row["Expected_Source_IDs"],
            "Retrieved_Source_IDs": ";".join(retrieved_ids),
            "Top_Relevance_Score": (
                f"{selected[0][1]:.4f}" if selected else ""
            ),
            "Source_Status": row["Source_Status"],
            "Retrieval_Result": outcome,
            "Expected_Sources_In_Staging": ";".join(
                sorted(set(expected_ids) & staged_ids)
            ),
        })

    fields = list(results[0].keys())
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)

    counts = {}
    for result in results:
        outcome = result["Retrieval_Result"]
        counts[outcome] = counts.get(outcome, 0) + 1

    in_scope = counts.get("MATCH", 0) + counts.get("MISS", 0)
    match_rate = (
        counts.get("MATCH", 0) / in_scope * 100 if in_scope else 0
    )

    report = [
        "# Department 3 Staged Retrieval Evaluation",
        "",
        f"- Questions evaluated: {len(results)}",
        f"- Model: {MODEL_ID}",
        f"- Model revision: {REVISION}",
        f"- Similarity: cosine (dot product on normalized vectors)",
        f"- Threshold: {THRESHOLD}",
        f"- Top K: {TOP_K} unique source documents",
        f"- Staged documents: {len(staged_ids)}",
        f"- Staged chunks: {len(chunks)}",
        f"- In-scope expected-source match rate: {match_rate:.2f}% ({counts.get('MATCH', 0)}/{in_scope})",
        "",
        "| Outcome | Questions |",
        "|---|---:|",
    ]
    for outcome in (
        "MATCH", "MISS", "OUT_OF_SCOPE",
        "SAFE_ABSTENTION", "REVIEW"
    ):
        report.append(f"| {outcome} | {counts.get(outcome, 0)} |")

    report += [
        "",
        "## Interpretation",
        "",
        "- OUT_OF_SCOPE means none of the expected source IDs exists in the staged index.",
        "- MATCH and MISS are calculated only when at least one expected source is staged.",
        "- REVIEW and SAFE_ABSTENTION apply to cases without a verified expected source.",
        "- This is a staged-vector benchmark, not an end-to-end chatbot answer evaluation.",
        "- Results are not directly comparable to the historical live FaqRetriever benchmark.",
        "",
        f"Detailed results: `{OUTPUT.relative_to(ROOT)}`",
    ]
    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")

    print(json.dumps({
        "questions": len(results),
        "outcomes": counts,
        "in_scope_match_rate_percent": round(match_rate, 2),
        "results_csv": str(OUTPUT),
        "report": str(REPORT),
    }, indent=2))


if __name__ == "__main__":
    main()
