"""
API tests for Part 2: every error response, regardless of source, shares
one envelope shape: {"error": {"code", "message", "details"}}.
"""


def _assert_envelope(body: dict, expected_code: str):
    assert "error" in body
    assert set(body["error"].keys()) == {"code", "message", "details"}
    assert body["error"]["code"] == expected_code


def test_404_uses_the_error_envelope(client, doctor_headers):
    response = client.get(
        "/patients/00000000-0000-0000-0000-000000000000", headers=doctor_headers
    )
    assert response.status_code == 404
    _assert_envelope(response.json(), "NOT_FOUND")


def test_401_uses_the_error_envelope(client):
    response = client.get("/auth/me")
    assert response.status_code == 401
    _assert_envelope(response.json(), "UNAUTHENTICATED")


def test_403_uses_the_error_envelope(client, doctor_headers):
    response = client.get("/reports/revenue", headers=doctor_headers)
    assert response.status_code == 403
    _assert_envelope(response.json(), "FORBIDDEN")


def test_422_validation_error_uses_the_error_envelope_and_lists_field_errors(client):
    response = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "x", "full_name": "", "role": "PATIENT"},
    )
    assert response.status_code == 422
    body = response.json()
    _assert_envelope(body, "VALIDATION_ERROR")
    assert isinstance(body["error"]["details"], list)
    assert len(body["error"]["details"]) > 0


def test_custom_field_validator_error_is_json_serializable(client, doctor_headers):
    """
    Regression test for a real bug found while building this module: a
    @field_validator raising ValueError embeds the actual exception
    OBJECT in Pydantic's error details, which plain json.dumps cannot
    serialize. This must not 500.
    """
    response = client.post(
        "/patients",
        json={
            "first_name": "Future",
            "last_name": "Person",
            "date_of_birth": "2999-01-01",
            "gender": None,
            "email": "future@example.com",
            "phone": "+92-300-0000000",
            "address": None,
            "blood_group": None,
        },
        headers=doctor_headers,
    )
    assert response.status_code == 422
    _assert_envelope(response.json(), "VALIDATION_ERROR")


def test_conflict_uses_the_error_envelope(client, doctor_headers, billing_headers):
    patient = client.post(
        "/patients",
        json={
            "first_name": "Conflict",
            "last_name": "Envelope",
            "date_of_birth": "1990-01-01",
            "gender": None,
            "email": "conflict.envelope@example.com",
            "phone": "+92-300-4444444",
            "address": None,
            "blood_group": None,
        },
        headers=doctor_headers,
    ).json()

    invoice = client.post(
        "/invoices", json={"patient_id": patient["id"], "amount": 10.00}, headers=billing_headers
    ).json()

    over = client.post(
        f"/invoices/{invoice['id']}/payments",
        json={"amount": 999.00, "payment_method": "CASH"},
        headers=billing_headers,
    )
    assert over.status_code == 400
    _assert_envelope(over.json(), "BAD_REQUEST")
