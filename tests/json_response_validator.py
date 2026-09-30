import json
from pydantic import ValidationError

from src.schemas import StructuredLLMResponse


def validate_json_response(raw_response: str) -> tuple[bool, str]:
    """Validate an LLM response against the strict JSON schema."""

    try:
        data = json.loads(raw_response)
        StructuredLLMResponse.model_validate(data)
        return True, "Valid JSON response"

    except json.JSONDecodeError:
        return False, "Invalid JSON syntax"

    except ValidationError as exc:
        return False, f"Schema validation failed: {exc}"


if __name__ == "__main__":
    test_cases = {
        "Valid JSON": """
        {
            "symptoms": ["fever", "headache"],
            "severity": "moderate",
            "message": "Please consult a doctor if symptoms persist."
        }
        """,

        "Malformed JSON": """
        {
            "symptoms": ["fever"],
            "severity": "mild",
            "message": "Please rest.
        }
        """,

        "Missing Field": """
        {
            "symptoms": ["fever"],
            "severity": "mild"
        }
        """,

        "Extra Field": """
        {
            "symptoms": ["fever"],
            "severity": "mild",
            "message": "Please rest.",
            "unexpected_field": "not allowed"
        }
        """,
    }

    for test_name, response in test_cases.items():
        is_valid, message = validate_json_response(response)
        print(f"{test_name}: Valid={is_valid}")
        print(f"  {message}")