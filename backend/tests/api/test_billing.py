"""API tests: invoice + payment flow, again mocking the (simulated)
external gateway so tests are fast and deterministic."""


class FakeGatewayClient:
    """A deterministic test double for PaymentGatewayClient - always confirms."""

    def confirm_payment(self, request) -> None:
        return None


def _create_patient(client, doctor_headers, email: str) -> str:
    response = client.post(
        "/patients",
        json={
            "first_name": "Billing",
            "last_name": "Patient",
            "date_of_birth": "1990-01-01",
            "gender": None,
            "email": email,
            "phone": "+92-300-6666666",
            "address": None,
            "blood_group": None,
        },
        headers=doctor_headers,
    )
    return response.json()["id"]


def test_full_invoice_payment_flow(client, monkeypatch, doctor_headers, billing_headers):
    # The real SimulatedPaymentGatewayClient has a genuine 15% random
    # failure rate - relying on simulate_failure=False alone would make
    # this test flaky (occasionally, correctly, declining). Mock it out
    # for a deterministic happy-path test, same reasoning as test_labs.py.
    monkeypatch.setattr(
        "app.services.payment_service.get_payment_gateway_client", lambda: FakeGatewayClient()
    )

    patient_id = _create_patient(client, doctor_headers, "billing.flow@example.com")

    invoice = client.post(
        "/invoices", json={"patient_id": patient_id, "amount": 100.00}, headers=billing_headers
    ).json()
    assert invoice["status"] == "UNPAID"

    payment = client.post(
        f"/invoices/{invoice['id']}/payments",
        json={"amount": 100.00, "payment_method": "CASH"},
        headers=billing_headers,
    ).json()
    payment_id = payment["payments"][0]["id"]
    assert payment["status"] == "UNPAID"  # still unpaid - payment is only PENDING so far

    confirmed = client.patch(
        f"/payments/{payment_id}/status", json={"simulate_failure": False}, headers=billing_headers
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "PAID"
    assert confirmed.json()["balance_due"] == "0.00"


def test_overpayment_is_rejected(client, doctor_headers, billing_headers):
    patient_id = _create_patient(client, doctor_headers, "billing.overpay@example.com")

    invoice = client.post(
        "/invoices", json={"patient_id": patient_id, "amount": 50.00}, headers=billing_headers
    ).json()

    response = client.post(
        f"/invoices/{invoice['id']}/payments",
        json={"amount": 999.00, "payment_method": "CARD"},
        headers=billing_headers,
    )
    assert response.status_code == 400


def test_forced_payment_decline(client, doctor_headers, billing_headers):
    patient_id = _create_patient(client, doctor_headers, "billing.decline@example.com")

    invoice = client.post(
        "/invoices", json={"patient_id": patient_id, "amount": 30.00}, headers=billing_headers
    ).json()
    payment = client.post(
        f"/invoices/{invoice['id']}/payments",
        json={"amount": 30.00, "payment_method": "CARD"},
        headers=billing_headers,
    ).json()
    payment_id = payment["payments"][0]["id"]

    declined = client.patch(
        f"/payments/{payment_id}/status", json={"simulate_failure": True}, headers=billing_headers
    )
    assert declined.status_code == 502


def test_doctor_cannot_access_billing(client, doctor_headers):
    response = client.get("/invoices", headers=doctor_headers)
    assert response.status_code == 403
