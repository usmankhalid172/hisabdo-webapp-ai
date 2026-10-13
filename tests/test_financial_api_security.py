def _financial_request(client, headers, user_id="user-42"):
    return client.post(
        "/api/v1/chatbot",
        headers=headers,
        json={
            "user_id": user_id,
            "message": "What is my balance?",
            "conversation_id": "security-test",
            "history": [],
        },
    )


def test_financial_query_requires_customer_identity(client, auth_headers):
    response = _financial_request(client, auth_headers)
    assert response.status_code == 401
    assert response.json()["error_code"] == "UNAUTHENTICATED_CUSTOMER"


def test_customer_cannot_request_another_account(client, auth_headers):
    headers = {
        **auth_headers,
        "X-Authenticated-User-ID": "user-99",
    }
    response = _financial_request(client, headers, user_id="user-42")
    assert response.status_code == 403
    assert response.json()["error_code"] == "CUSTOMER_ACCESS_DENIED"


def test_matching_customer_identity_is_accepted(client, auth_headers):
    headers = {
        **auth_headers,
        "X-Authenticated-User-ID": "user-42",
    }
    response = _financial_request(client, headers)
    assert response.status_code == 200


def test_financial_query_still_requires_internal_token(client):
    response = _financial_request(
        client,
        {"X-Authenticated-User-ID": "user-42"},
    )
    assert response.status_code == 401
