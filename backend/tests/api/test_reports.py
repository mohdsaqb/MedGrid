"""API tests: reporting endpoints, and their ADMIN-only access rule."""


def test_admin_can_view_all_reports(client, admin_headers):
    for path in [
        "/reports/patients",
        "/reports/appointments",
        "/reports/labs",
        "/reports/revenue",
        "/reports/doctor-performance",
    ]:
        response = client.get(path, headers=admin_headers)
        assert response.status_code == 200, f"{path} failed: {response.text}"


def test_reports_reflect_real_data(client, admin_headers, doctor_headers):
    client.post(
        "/patients",
        json={
            "first_name": "Report",
            "last_name": "Subject",
            "date_of_birth": "1990-01-01",
            "gender": None,
            "email": "report.subject@example.com",
            "phone": "+92-300-5555555",
            "address": None,
            "blood_group": None,
        },
        headers=doctor_headers,
    )

    report = client.get("/reports/patients", headers=admin_headers).json()
    assert report["total_patients"] >= 1


def test_non_admin_roles_cannot_view_reports(
    client, doctor_headers, billing_headers, lab_tech_headers, patient_role_headers
):
    for headers in [doctor_headers, billing_headers, lab_tech_headers, patient_role_headers]:
        response = client.get("/reports/revenue", headers=headers)
        assert response.status_code == 403
