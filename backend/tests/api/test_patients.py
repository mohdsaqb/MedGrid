"""API tests: patient creation, duplicate patient, unauthorized access."""

from datetime import date


def _sample_payload(**overrides) -> dict:
    payload = {
        "first_name": "Sana",
        "last_name": "Malik",
        "date_of_birth": "1992-05-15",
        "gender": None,
        "email": "sana.api-test@example.com",
        "phone": "+92-321-5551234",
        "address": None,
        "blood_group": None,
    }
    payload.update(overrides)
    return payload


def test_doctor_can_create_patient(client, doctor_headers):
    response = client.post("/patients", json=_sample_payload(), headers=doctor_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["patient_number"].startswith("PT-")


def test_duplicate_patient_email_rejected(client, doctor_headers):
    payload = _sample_payload(email="duplicate-patient@example.com")
    first = client.post("/patients", json=payload, headers=doctor_headers)
    assert first.status_code == 201

    second = client.post(
        "/patients", json=_sample_payload(first_name="Other", email="duplicate-patient@example.com"), headers=doctor_headers
    )
    assert second.status_code == 400


def test_creating_patient_with_future_dob_is_rejected(client, doctor_headers):
    future_dob = date.today().replace(year=date.today().year + 1).isoformat()
    response = client.post(
        "/patients", json=_sample_payload(date_of_birth=future_dob), headers=doctor_headers
    )
    assert response.status_code == 422


def test_lab_technician_cannot_create_patient(client, lab_tech_headers):
    response = client.post("/patients", json=_sample_payload(), headers=lab_tech_headers)
    assert response.status_code == 403


def test_unauthenticated_request_cannot_create_patient(client):
    response = client.post("/patients", json=_sample_payload())
    assert response.status_code == 401


def test_billing_staff_can_read_but_not_write_patients(client, doctor_headers, billing_headers):
    created = client.post("/patients", json=_sample_payload(), headers=doctor_headers).json()

    read = client.get(f"/patients/{created['id']}", headers=billing_headers)
    assert read.status_code == 200

    write = client.put(
        f"/patients/{created['id']}", json=_sample_payload(first_name="Changed"), headers=billing_headers
    )
    assert write.status_code == 403
