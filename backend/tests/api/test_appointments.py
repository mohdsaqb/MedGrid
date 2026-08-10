"""API test: the doctor double-booking conflict rule from Module 5."""

from datetime import date, timedelta


def _future_date() -> str:
    return (date.today() + timedelta(days=30)).isoformat()


def _create_doctor(client, admin_headers) -> str:
    response = client.post(
        "/doctors",
        json={
            "name": "Dr. Test Conflict",
            "specialization": "Cardiology",
            "department": "Cardiology",
            "license_number": "LIC-TEST-001",
            "email": "dr.conflict@example.com",
            "phone": "+92-300-9999999",
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_patient(client, doctor_headers, email: str) -> str:
    response = client.post(
        "/patients",
        json={
            "first_name": "Conflict",
            "last_name": "Test",
            "date_of_birth": "1990-01-01",
            "gender": None,
            "email": email,
            "phone": "+92-300-1111111",
            "address": None,
            "blood_group": None,
        },
        headers=doctor_headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_double_booking_same_doctor_same_slot_is_rejected(client, admin_headers, doctor_headers):
    doctor_id = _create_doctor(client, admin_headers)
    patient_a = _create_patient(client, doctor_headers, "conflict.a@example.com")
    patient_b = _create_patient(client, doctor_headers, "conflict.b@example.com")

    slot = {"appointment_date": _future_date(), "appointment_time": "10:00:00", "reason": "Checkup"}

    first = client.post(
        "/appointments",
        json={"patient_id": patient_a, "doctor_id": doctor_id, **slot},
        headers=doctor_headers,
    )
    assert first.status_code == 201

    second = client.post(
        "/appointments",
        json={"patient_id": patient_b, "doctor_id": doctor_id, **slot},
        headers=doctor_headers,
    )
    assert second.status_code == 409


def test_cancelling_then_rebooking_same_slot_succeeds(client, admin_headers, doctor_headers):
    doctor_id = _create_doctor(client, admin_headers)
    patient_a = _create_patient(client, doctor_headers, "conflict.c@example.com")
    patient_b = _create_patient(client, doctor_headers, "conflict.d@example.com")

    slot = {"appointment_date": _future_date(), "appointment_time": "11:00:00", "reason": "Checkup"}

    first = client.post(
        "/appointments",
        json={"patient_id": patient_a, "doctor_id": doctor_id, **slot},
        headers=doctor_headers,
    )
    appointment_id = first.json()["id"]

    cancel = client.patch(
        f"/appointments/{appointment_id}/status", json={"status": "CANCELLED"}, headers=doctor_headers
    )
    assert cancel.status_code == 200

    rebooked = client.post(
        "/appointments",
        json={"patient_id": patient_b, "doctor_id": doctor_id, **slot},
        headers=doctor_headers,
    )
    assert rebooked.status_code == 201
