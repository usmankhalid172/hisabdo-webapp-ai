from tests.json_response_validator import validate_json_response


def test_valid_json_response():
    response = """
    {
        "symptoms": ["fever", "headache"],
        "severity": "moderate",
        "message": "Please consult a doctor."
    }
    """

    is_valid, _ = validate_json_response(response)

    assert is_valid is True


def test_malformed_json_is_rejected():
    response = """
    {
        "symptoms": ["fever"],
        "severity": "mild",
        "message": "Please rest.
    """

    is_valid, _ = validate_json_response(response)

    assert is_valid is False


def test_missing_required_field_is_rejected():
    response = """
    {
        "symptoms": ["fever"],
        "severity": "mild"
    }
    """

    is_valid, _ = validate_json_response(response)

    assert is_valid is False


def test_extra_field_is_rejected():
    response = """
    {
        "symptoms": ["fever"],
        "severity": "mild",
        "message": "Please rest.",
        "unexpected_field": "not allowed"
    }
    """

    is_valid, _ = validate_json_response(response)

    assert is_valid is False