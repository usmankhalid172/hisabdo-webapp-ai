
import json
from pathlib import Path

from advanced_retrieval import (
    retrieve,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    ndcg_at_k,
)

BASE_DIR = Path(__file__).parent
DATASET_PATH = (
    BASE_DIR / "knowledge_base" / "evaluation_dataset.json"
)

TOP_K = 3
THRESHOLD = 0.15

METHODS = ["semantic", "lexical", "hybrid"]


def evaluate():
    with open(DATASET_PATH, encoding="utf-8") as file:
        dataset = json.load(file)

    results_summary = {}

    for method in METHODS:
        precisions = []
        recalls = []
        reciprocal_ranks = []
        ndcgs = []
        unrelated_returns = 0

        print(f"\n{'=' * 55}")
        print(f"METHOD: {method.upper()}")
        print("=" * 55)

        for case in dataset["cases"]:
            query = case["query"]
            relevant = case["relevant_ids"]

            results = retrieve(
                query,
                method=method,
                top_k=TOP_K,
                threshold=THRESHOLD,
            )

            retrieved_ids = [
                item["document_id"] for item in results
            ]

            precision = precision_at_k(
                retrieved_ids, relevant, TOP_K
            )
            recall = recall_at_k(
                retrieved_ids, relevant, TOP_K
            )
            mrr = reciprocal_rank(
                retrieved_ids, relevant
            )
            ndcg = ndcg_at_k(
                retrieved_ids, relevant, TOP_K
            )

            if not relevant and retrieved_ids:
                unrelated_returns += 1

            precisions.append(precision)
            recalls.append(recall)
            reciprocal_ranks.append(mrr)
            ndcgs.append(ndcg)

            print(f"\nQuery: {query}")
            print(f"Expected: {relevant}")
            print(f"Retrieved: {retrieved_ids}")
            print(
                f"Precision@{TOP_K}: {precision:.3f} | "
                f"Recall@{TOP_K}: {recall:.3f} | "
                f"MRR: {mrr:.3f} | "
                f"nDCG@{TOP_K}: {ndcg:.3f}"
            )

        count = len(dataset["cases"])

        summary = {
            "precision_at_3": sum(precisions) / count,
            "recall_at_3": sum(recalls) / count,
            "mrr": sum(reciprocal_ranks) / count,
            "ndcg_at_3": sum(ndcgs) / count,
            "unrelated_false_returns": unrelated_returns,
        }

        results_summary[method] = summary

    print("\n\nFINAL COMPARISON")
    print("=" * 75)

    for method, metrics in results_summary.items():
        print(f"\n{method.upper()}")
        for name, value in metrics.items():
            print(f"{name}: {value:.4f}")

    output_path = BASE_DIR / "retrieval_evaluation_results.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(results_summary, file, indent=4)

    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    evaluate()
