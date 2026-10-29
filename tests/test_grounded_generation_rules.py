from src.financial_assistant.prompts import SYSTEM_PROMPT


def test_prompt_has_conflicting_source_rules():
    prompt = SYSTEM_PROMPT.lower()
    assert "conflict" in prompt
    assert "source" in prompt
    assert "review" in prompt


def test_prompt_has_grounded_evidence_rules():
    prompt = SYSTEM_PROMPT.lower()
    assert "retrieved context" in prompt
    assert "cannot be confirmed from the available knowledge" in prompt


def test_prompt_has_ambiguity_clarification_rules():
    prompt = SYSTEM_PROMPT.lower()
    assert "clarification" in prompt


def test_prompt_has_private_financial_data_protection():
    prompt = SYSTEM_PROMPT.lower()
    assert "another user" in prompt

