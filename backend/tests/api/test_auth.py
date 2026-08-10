"""API tests: registration, login, invalid password, and authorization."""


def test_registration_succeeds(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "CorrectHorse123",
            "full_name": "New User",
            "role": "PATIENT",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "newuser@example.com"
    # The password must never come back in any response, hashed or not.
    assert "password" not in body
    assert "hashed_password" not in body


def test_registration_rejects_duplicate_email(client):
    payload = {
        "email": "dup@example.com",
        "password": "CorrectHorse123",
        "full_name": "First",
        "role": "PATIENT",
    }
    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/auth/register", json={**payload, "full_name": "Second"})
    assert second.status_code == 400


def test_login_succeeds_with_correct_credentials(client):
    client.post(
        "/auth/register",
        json={
            "email": "logintest@example.com",
            "password": "CorrectHorse123",
            "full_name": "Login Test",
            "role": "DOCTOR",
        },
    )

    response = client.post(
        "/auth/login",
        data={"username": "logintest@example.com", "password": "CorrectHorse123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_fails_with_invalid_password(client):
    client.post(
        "/auth/register",
        json={
            "email": "wrongpass@example.com",
            "password": "CorrectHorse123",
            "full_name": "Test",
            "role": "DOCTOR",
        },
    )

    response = client.post(
        "/auth/login",
        data={"username": "wrongpass@example.com", "password": "TotallyWrongPassword"},
    )
    assert response.status_code == 401
    # (Response body SHAPE is asserted separately in test_error_handling.py,
    # once Part 2 gives every error a consistent envelope.)


def test_protected_endpoint_rejects_missing_token(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_protected_endpoint_rejects_garbage_token(client):
    response = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_protected_endpoint_accepts_valid_token(client, doctor_headers):
    response = client.get("/auth/me", headers=doctor_headers)
    assert response.status_code == 200
    assert response.json()["role"] == "DOCTOR"
