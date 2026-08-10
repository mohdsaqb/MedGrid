"""
API tests: lab order + lab result, using a MOCKED LIMS client.

Why mocking matters here concretely: SimulatedLimsClient (Module 7) has a
real time.sleep() and a real random chance of failure. Without mocking,
these tests would be slow AND flaky - sometimes failing for no reason
related to our code. Because lab_order_service depends on the LimsClient
INTERFACE (not the concrete simulated class), substituting a fake for the
test is trivial - this is Module 7's integration-boundary lesson paying
off directly.
"""

from app.integrations.lims.schemas import LimsOrderRequest, LimsOrderResult


class FakeLimsClient:
    """A deterministic test double - no sleep, no randomness."""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail

    def process_order(self, request: LimsOrderRequest) -> LimsOrderResult:
        if self.should_fail:
            from app.integrations.lims.exceptions import LimsServiceError

            raise LimsServiceError("Fake LIMS failure for testing")
        return LimsOrderResult(result="7.8", unit="x10^9/L", reference_range="4.5-11.0")


def _create_doctor(client, admin_headers) -> str:
    response = client.post(
        "/doctors",
        json={
            "name": "Dr. Lab Test",
            "specialization": "Pathology",
            "department": "Pathology",
            "license_number": "LIC-LAB-001",
            "email": "dr.lab@example.com",
            "phone": "+92-300-8888888",
        },
        headers=admin_headers,
    )
    return response.json()["id"]


def _create_patient(client, doctor_headers) -> str:
    response = client.post(
        "/patients",
        json={
            "first_name": "Lab",
            "last_name": "Patient",
            "date_of_birth": "1990-01-01",
            "gender": None,
            "email": "lab.patient@example.com",
            "phone": "+92-300-7777777",
            "address": None,
            "blood_group": None,
        },
        headers=doctor_headers,
    )
    return response.json()["id"]


def _create_lab_test(client, admin_headers) -> str:
    response = client.post(
        "/lab-tests",
        json={
            "name": "Complete Blood Count (CBC) - Test",
            "description": None,
            "price": 25.00,
            "normal_range": "4.5-11.0",
        },
        headers=admin_headers,
    )
    return response.json()["id"]


def test_lab_order_and_result_happy_path(
    client, monkeypatch, admin_headers, doctor_headers, lab_tech_headers
):
    doctor_id = _create_doctor(client, admin_headers)
    patient_id = _create_patient(client, doctor_headers)
    test_id = _create_lab_test(client, admin_headers)

    order = client.post(
        "/lab-orders",
        json={"patient_id": patient_id, "doctor_id": doctor_id, "test_id": test_id},
        headers=doctor_headers,
    )
    assert order.status_code == 201
    assert order.json()["status"] == "PENDING"
    order_id = order.json()["id"]

    # Patch WHERE THE NAME IS LOOKED UP (lab_order_service's own imported
    # reference), not where it's originally defined - a classic, real
    # Python mocking gotcha.
    monkeypatch.setattr(
        "app.services.lab_order_service.get_lims_client", lambda: FakeLimsClient()
    )

    processed = client.post(
        f"/lab-orders/{order_id}/process", json={"simulate_failure": False}, headers=lab_tech_headers
    )
    assert processed.status_code == 200
    body = processed.json()
    assert body["status"] == "COMPLETED"
    assert body["result"]["result"] == "7.8"


def test_lab_order_processing_failure_is_handled(
    client, monkeypatch, admin_headers, doctor_headers, lab_tech_headers
):
    doctor_id = _create_doctor(client, admin_headers)
    patient_id = _create_patient(client, doctor_headers)
    test_id = _create_lab_test(client, admin_headers)

    order = client.post(
        "/lab-orders",
        json={"patient_id": patient_id, "doctor_id": doctor_id, "test_id": test_id},
        headers=doctor_headers,
    ).json()

    monkeypatch.setattr(
        "app.services.lab_order_service.get_lims_client", lambda: FakeLimsClient(should_fail=True)
    )

    processed = client.post(
        f"/lab-orders/{order['id']}/process", json={"simulate_failure": False}, headers=lab_tech_headers
    )
    assert processed.status_code == 502


def test_doctor_cannot_process_lab_orders(client, admin_headers, doctor_headers):
    doctor_id = _create_doctor(client, admin_headers)
    patient_id = _create_patient(client, doctor_headers)
    test_id = _create_lab_test(client, admin_headers)

    order = client.post(
        "/lab-orders",
        json={"patient_id": patient_id, "doctor_id": doctor_id, "test_id": test_id},
        headers=doctor_headers,
    ).json()

    response = client.post(
        f"/lab-orders/{order['id']}/process", json={"simulate_failure": False}, headers=doctor_headers
    )
    assert response.status_code == 403
