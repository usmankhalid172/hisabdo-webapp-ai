import sys
from pathlib import Path

# Add the project root to Python's import path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.financial_assistant.rag.knowledge_base import load_knowledge_base
from src.financial_assistant.rag.retriever import FinancialRetriever


DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "sample_financial_knowledge.json"
)


documents = load_knowledge_base(str(DATA_PATH))
retriever = FinancialRetriever(documents)

queries = [
    "How do I calculate profit?",
    "What is revenue?",
    "Why should I track customer balances?",
    "How can I understand my business expenses?"
]

for query in queries:
    print(f"\nQuery: {query}")

    results = retriever.retrieve(query, top_k=2)

    for result in results:
        print(
            f"- {result['id']} | "
            f"score={result['score']} | "
            f"{result['answer']}"
        )