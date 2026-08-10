"""
UNIT tests for the Module 9 mapping layer. These construct a Patient
object directly in memory (never added to a session, never saved) - a
SQLAlchemy model is just a plain Python object until you add() it. This
is the clearest kind of unit test: the mapper is a pure function, so we
can test it with zero database involvement at all.
"""

import uuid
from datetime import date

from app.integrations.fhir.mappers import map_patient_to_fhir
from app.models.patient import Gender, Patient


def _make_patient(**overrides) -> Patient:
    defaults = dict(
        id=uuid.uuid4(),
        patient_number="PT-000999",
        first_name="Ayesha",
        last_name="Khan",
        date_of_birth=date(1990, 4, 12),
        gender=Gender.FEMALE,
        email="ayesha@example.com",
        phone="+92-300-1234567",
    )
    defaults.update(overrides)
    return Patient(**defaults)


def test_map_patient_to_fhir_shape():
    patient = _make_patient()
    resource = map_patient_to_fhir(patient)

    assert resource.resourceType == "Patient"
    assert resource.id == str(patient.id)
    assert resource.name == [{"family": "Khan", "given": ["Ayesha"]}]
    assert resource.gender == "female"
    assert resource.birthDate == "1990-04-12"


def test_map_patient_to_fhir_gender_mapping():
    # Internal enum value differs from FHIR's own vocabulary in general -
    # for FEMALE they happen to look similar; this locks in the mapping
    # table itself is doing the translation, not a coincidence.
    for internal, expected in [
        (Gender.MALE, "male"),
        (Gender.FEMALE, "female"),
        (Gender.OTHER, "other"),
        (Gender.UNKNOWN, "unknown"),
    ]:
        resource = map_patient_to_fhir(_make_patient(gender=internal))
        assert resource.gender == expected


def test_map_patient_to_fhir_omits_missing_contact_points():
    patient = _make_patient(email=None)
    resource = map_patient_to_fhir(patient)
    systems = [t["system"] for t in resource.telecom]
    assert "email" not in systems
    assert "phone" in systems
