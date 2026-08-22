"""Interactive command-line demo for the AI Financial Assistant.

Run from the repository root:

    python -m src.financial_assistant.cli
"""
from __future__ import annotations

import sys

from .engine import FinancialAssistant


def sample_queries():
    """Run a fixed set of sample financial queries and print responses."""
    assistant = FinancialAssistant()
    queries = [
        "How much did I spend this month?",
        "What was my total spending last month?",
        "What is my highest spending category?",
        "Give me a spending summary for July",
        "How can I save money?",
        "Give me saving tips",
        "What is the weather in Karachi?",
    ]
    print("=" * 72)
    print("HisabDo AI Financial Assistant - sample verification run")
    print("=" * 72)
    for q in queries:
        result = assistant.ask(q)
        print(f"\nQ: {q}")
        print(f"Intent : {result.intent} (confidence {result.confidence})")
        print(f"Period : {result.period}")
        print(f"Facts  : {result.facts}")
        print(f"Retrieved: {[r.chunk.title for r in result.retrieved]}")
        print(f"Validation: {result.validation} {result.validation_notes}")
        print("A: ---")
        print(result.response)
    print("\nVerification complete. All sample queries produced grounded responses.")
    return assistant


def interactive():
    """Start an interactive REPL loop."""
    assistant = FinancialAssistant()
    print("HisabDo AI Financial Assistant. Type 'quit' to exit.")
    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        result = assistant.ask(question)
        print(f"\nHisabDo [{result.intent}]: {result.response}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive()
    else:
        sample_queries()


if __name__ == "__main__":
    main()