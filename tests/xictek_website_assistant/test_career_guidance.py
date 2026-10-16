import json
from pathlib import Path

from src.xictek_website_assistant.llm_client import GroqLLMProvider
from src.xictek_website_assistant.prompts import SYSTEM_PROMPT, build_system_prompt


def test_careers_evaluation_suite_has_required_scenarios_and_checks():
    suite_path = (
        Path(__file__).resolve().parents[1]
        / "evaluation"
        / "careers_job_openings_test_cases.json"
    )
    suite = json.loads(suite_path.read_text(encoding="utf-8"))
    cases = suite["cases"]
    ids = [case["test_id"] for case in cases]
    scenarios = " ".join(case["scenario"].lower() for case in cases)

    assert len(cases) == 10
    assert len(ids) == len(set(ids))
    assert all(case["must_pass"] and case["must_not"] for case in cases)
    assert "eligibility" in scenarios
    assert "process" in scenarios
    assert "deadline" in scenarios
    assert "not hiring" in scenarios
    assert any(
        "clickable" in check.lower() and "mailto:" in check.lower()
        for case in cases
        for check in case["must_pass"]
    )


def test_career_prompt_includes_direct_xictek_cv_submission_guidance():
    prompt = build_system_prompt("What job openings do you have, and where should I send my CV?")

    assert prompt.startswith(SYSTEM_PROMPT)
    assert "email their CV to [xicteksystems@gmail.com](mailto:xicteksystems@gmail.com)" in prompt
    assert "[xicteksystems@gmail.com](mailto:xicteksystems@gmail.com)" in prompt
    assert "clickable Markdown link" in prompt
    assert "use the URL exactly as provided" in prompt
    assert "label it as the contact page" in prompt
    assert "including when the only online route is a general contact page" in prompt
    assert "name the role in the email" in prompt
    assert "Do not invent application requirements, deadlines, hiring status, or URLs" in prompt
    assert "do not present xictek's email as a hisabdo application address" in prompt.lower()


def test_non_career_prompt_does_not_add_application_guidance():
    assert build_system_prompt("What services does XICTEK offer?") == SYSTEM_PROMPT


def test_groq_provider_uses_career_specific_prompt(monkeypatch):
    captured = {}

    class _Response:
        def json(self):
            return {"choices": [{"message": {"content": "Email your CV."}}]}

    def fake_post_with_retry(url, **kwargs):
        captured.update(kwargs)
        return _Response()

    monkeypatch.setattr(
        "src.xictek_website_assistant.llm_client._post_with_retry",
        fake_post_with_retry,
    )

    reply, _ = GroqLLMProvider("test-key").generate_reply(
        "How do I apply for a job?",
        context="Open roles: Senior Full-Stack Developer.",
    )

    assert reply == "Email your CV."
    system_message = captured["json"]["messages"][0]
    assert system_message["role"] == "system"
    assert "xicteksystems@gmail.com" in system_message["content"]
