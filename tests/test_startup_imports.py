"""Startup import validation — catches deployment import errors early."""


def test_get_retriever_importable():
    from src.financial_assistant.rag import get_retriever
    assert callable(get_retriever)
