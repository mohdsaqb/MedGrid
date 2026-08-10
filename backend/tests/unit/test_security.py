"""
UNIT tests: pure functions only - no database, no HTTP, no network.
These should be the fastest tests in the suite, and don't need any
fixture from conftest.py beyond what Python itself provides.
"""

from app.utils.password import hash_password, verify_password


def test_hash_password_does_not_return_plaintext():
    hashed = hash_password("CorrectHorse123")
    assert hashed != "CorrectHorse123"


def test_verify_password_accepts_correct_password():
    hashed = hash_password("CorrectHorse123")
    assert verify_password("CorrectHorse123", hashed) is True


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("CorrectHorse123")
    assert verify_password("WrongPassword", hashed) is False


def test_same_password_hashes_differently_each_time():
    # Argon2 embeds a random salt per hash - two hashes of the same
    # password must never be byte-identical, or a rainbow-table style
    # attack becomes possible.
    first = hash_password("CorrectHorse123")
    second = hash_password("CorrectHorse123")
    assert first != second
    assert verify_password("CorrectHorse123", first) is True
    assert verify_password("CorrectHorse123", second) is True
