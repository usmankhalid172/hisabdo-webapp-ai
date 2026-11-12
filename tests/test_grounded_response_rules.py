from src.financial_assistant.service import (
    _is_ambiguous_expense_query,
    _resolve_source_conflicts,
    _citation_supports_reply,
)


def test_bare_expense_query_requires_clarification():
    assert _is_ambiguous_expense_query("expense")
    assert _is_ambiguous_expense_query("Show expenses")
    assert not _is_ambiguous_expense_query("How do I categorize an expense?")


def test_unresolved_source_conflict_is_not_silently_selected():
    sources = [
        {"id": "a", "conflict_group": "expense_rule", "text": "Rule A"},
        {"id": "b", "conflict_group": "expense_rule", "text": "Rule B"},
    ]
    assert _resolve_source_conflicts(sources) is None


def test_unique_source_priority_resolves_conflict():
    sources = [
        {"id": "a", "conflict_group": "expense_rule", "source_priority": 1},
        {"id": "b", "conflict_group": "expense_rule", "source_priority": 2},
    ]
    result = _resolve_source_conflicts(sources)
    assert [item["id"] for item in result] == ["b"]


def test_equal_source_priority_remains_unresolved():
    sources = [
        {"id": "a", "conflict_group": "expense_rule", "source_priority": 2},
        {"id": "b", "conflict_group": "expense_rule", "source_priority": 2},
    ]
    assert _resolve_source_conflicts(sources) is None


def test_citation_requires_matching_source_evidence():
    source = {
        "title": "Automatic expense categorization",
        "text": "HisabDo predicts an expense category using rule based matching and a machine learning model.",
    }
    assert _citation_supports_reply(
        "HisabDo predicts an expense category using rule based matching.",
        source,
    )


def test_unrelated_reply_does_not_receive_source_citation():
    source = {
        "title": "Automatic expense categorization",
        "text": "HisabDo predicts an expense category using rule based matching.",
    }
    assert not _citation_supports_reply(
        "You can change your account password in settings.",
        source,
    )
