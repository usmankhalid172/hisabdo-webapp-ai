import csv
import math
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.financial_assistant.faq_rag import get_retriever

DATASET = ROOT / "docs/evaluation/department3_evaluation_set_v1.0.csv"
OUTPUT = ROOT / "docs/evaluation/department3_latency_benchmark.csv"
SUMMARY = ROOT / "docs/evaluation/department3_latency_summary.md"

with DATASET.open("r", encoding="utf-8-sig", newline="") as file:
    rows = [
        row for row in csv.DictReader(file)
        if row.get("Source_Status", "").strip().lower() == "verified"
        and row.get("Question", "").strip()
    ]

if not rows:
    raise SystemExit("No verified questions found in the evaluation dataset.")

print(f"Verified questions: {len(rows)}")
print("Loading FAQ retriever and local embedding model...")

retriever = get_retriever()

# One warm-up call; excluded from measured results.
retriever.retrieve(rows[0]["Question"])

results = []

for row in rows:
    started = time.perf_counter()
    retrieved = retriever.retrieve(row["Question"])
    latency = (time.perf_counter() - started) * 1000

    expected = {
        item.strip()
        for item in row.get("Supporting_Source_Records", "").split(";")
        if item.strip()
    }
    actual = {
        item.get("id")
        for item in retrieved
        if isinstance(item, dict) and item.get("id")
    }

    results.append({
        "Test_ID": row.get("Test_ID", ""),
        "Latency_ms": round(latency, 2),
        "Outcome": "success" if retrieved else "empty",
        "Retrieved_Source_IDs": ";".join(sorted(actual)),
        "Expected_Source_IDs": ";".join(sorted(expected)),
        "Any_Source_Match": bool(expected & actual),
    })

latencies = sorted(item["Latency_ms"] for item in results)
p95_index = max(0, math.ceil(0.95 * len(latencies)) - 1)

with OUTPUT.open("w", encoding="utf-8-sig", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=list(results[0].keys()))
    writer.writeheader()
    writer.writerows(results)

success_count = sum(item["Outcome"] == "success" for item in results)
empty_count = len(results) - success_count
match_count = sum(item["Any_Source_Match"] for item in results)

summary = [
    "# Department 3 Local Retrieval Latency Benchmark",
    "",
    "- Scope: local FAQ retrieval only; excludes full chatbot and external API latency.",
    "- Dataset: verified questions from department3_evaluation_set_v1.0.csv.",
    "- Runs: one measured retrieval per verified question; one warm-up excluded.",
    "- Embeddings: configured local FAQ embedding model.",
    "",
    "## Results",
    "",
    f"- Verified questions measured: {len(results)}",
    f"- Retrieval success: {success_count}",
    f"- Empty retrievals: {empty_count}",
    f"- Average latency: {statistics.mean(latencies):.2f} ms",
    f"- Median latency (p50): {statistics.median(latencies):.2f} ms",
    f"- p95 latency: {latencies[p95_index]:.2f} ms",
    f"- Maximum latency: {max(latencies):.2f} ms",
    f"- Questions with at least one expected source matched: {match_count}/{len(results)}",
    "",
    "## Limitations",
    "",
    "- This is a local single-run-per-question measurement, not a load test.",
    "- Source match is not answer accuracy.",
    "- External provider/API latency and monetary cost were not measured.",
    "- Results depend on the local machine and current runtime conditions.",
]

SUMMARY.write_text("\n".join(summary) + "\n", encoding="utf-8")

print("\n".join(summary))
print(f"\nDetailed results: {OUTPUT}")
print(f"Summary: {SUMMARY}")
