from src.xictek_website_assistant.llm_client import GroqLLMProvider
from src.xictek_website_assistant.prompts import SYSTEM_PROMPT, build_system_prompt


def test_career_prompt_includes_direct_xictek_cv_submission_guidance():
    prompt = build_system_prompt("What job openings do you have, and where should I send my CV?")

    assert prompt.startswith(SYSTEM_PROMPT)
    assert "email your CV to xicteksystems@gmail.com" in prompt
    assert "name the role in the email" in prompt
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
