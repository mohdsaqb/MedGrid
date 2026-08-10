"""
Pure mapping functions: internal ORM object in, FHIR-shaped Pydantic
model out. No database access, no I/O, no side effects - see Module 9's
teaching on why mapping layers are kept pure (trivially unit-testable,
and internal/external changes each only ever touch this one file).
"""

from app.integrations.fhir.resources import FHIREncounter, FHIRObservation, FHIRPatient
from app.models.encounter import Encounter, EncounterStatus
from app.models.lab_order import LabOrder
from app.models.patient import Gender, Patient

# Internal enum value -> FHIR's own coded vocabulary. Worth noticing these
# are NOT always the same strings, even when the concept matches exactly -
# a concrete example of Part A's "internal vs external representation".
_GENDER_TO_FHIR = {
    Gender.MALE: "male",
    Gender.FEMALE: "female",
    Gender.OTHER: "other",
    Gender.UNKNOWN: "unknown",
}

_ENCOUNTER_STATUS_TO_FHIR = {
    EncounterStatus.OPEN: "in-progress",
    EncounterStatus.CLOSED: "finished",
}


def map_patient_to_fhir(patient: Patient) -> FHIRPatient:
    telecom = []
    if patient.phone:
        telecom.append({"system": "phone", "value": patient.phone})
    if patient.email:
        telecom.append({"system": "email", "value": patient.email})

    return FHIRPatient(
        id=str(patient.id),
        identifier=[{"system": "urn:medgrid:patient-number", "value": patient.patient_number}],
        name=[{"family": patient.last_name, "given": [patient.first_name]}],
        gender=_GENDER_TO_FHIR.get(patient.gender, "unknown"),
        birthDate=patient.date_of_birth.isoformat(),
        telecom=telecom,
    )


def map_encounter_to_fhir(encounter: Encounter) -> FHIREncounter:
    return FHIREncounter(
        id=str(encounter.id),
        status=_ENCOUNTER_STATUS_TO_FHIR[encounter.status],
        class_={
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "AMB",
            "display": "ambulatory",
        },
        subject={"reference": f"Patient/{encounter.patient_id}"},
        participant=[
            {
                "individual": {
                    "reference": f"Practitioner/{encounter.doctor_id}",
                    "display": encounter.doctor.name,
                }
            }
        ],
        period={"start": encounter.encounter_date.isoformat()},
        reasonCode=[{"text": encounter.diagnosis}],
    )


def map_lab_result_to_fhir_observation(lab_order: LabOrder) -> FHIRObservation:
    """
    Requires lab_order.result to already be loaded and present - callers
    (see fhir_export_service.py) are responsible for only calling this
    once a result actually exists.
    """
    result = lab_order.result
    value_kwargs: dict = {}
    try:
        value_kwargs["valueQuantity"] = {"value": float(result.result), "unit": result.unit or ""}
    except ValueError:
        # Not every lab result is numeric - "Positive"/"Reactive"/"Trace"
        # are common real qualitative results (same reasoning as
        # LabResult.result being a string column, Module 7).
        value_kwargs["valueString"] = result.result

    return FHIRObservation(
        id=str(lab_order.id),
        status="final",
        code={"text": lab_order.test.name},
        subject={"reference": f"Patient/{lab_order.patient_id}"},
        performer=[{"reference": f"Practitioner/{lab_order.doctor_id}"}],
        effectiveDateTime=lab_order.ordered_at.isoformat(),
        referenceRange=[{"text": result.reference_range}] if result.reference_range else [],
        **value_kwargs,
    )
