"""
INTEGRATION tests: real service functions against a real (test) database
session, but calling Python functions directly - no HTTP, no routing, no
auth layer. This catches real SQL/ORM bugs that a pure unit test
(no database at all) cannot, while running faster and failing with a
clearer traceback than a full API test would.
"""

from datetime import date

import pytest

from app.schemas.patient import PatientCreate
from app.services.patient_service import DuplicateEmailError, create_patient, get_patient


def _sample_patient_data(**overrides) -> PatientCreate:
    defaults = dict(
        first_name="Bilal",
        last_name="Ahmed",
        date_of_birth=date(1985, 6, 20),
        gender=None,
        email="bilal.integration@example.com",
        phone="+92-300-1112222",
        address=None,
        blood_group=None,
    )
    defaults.update(overrides)
    return PatientCreate(**defaults)


def test_create_patient_persists_and_generates_patient_number(db_session):
    created = create_patient(db_session, _sample_patient_data())

    assert created.patient_number.startswith("PT-")

    fetched = get_patient(db_session, created.id)
    assert fetched.email == "bilal.integration@example.com"


def test_duplicate_email_is_rejected(db_session):
    create_patient(db_session, _sample_patient_data(email="dupe@example.com"))

    with pytest.raises(DuplicateEmailError):
        create_patient(
            db_session,
            _sample_patient_data(first_name="Someone", last_name="Else", email="dupe@example.com"),
        )
