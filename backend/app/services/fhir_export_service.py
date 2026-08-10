import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.integrations.fhir.mappers import (
    map_encounter_to_fhir,
    map_lab_result_to_fhir_observation,
    map_patient_to_fhir,
)
from app.integrations.health_exchange import get_health_exchange_client
from app.integrations.health_exchange.exceptions import HealthExchangeError
from app.models.encounter import Encounter
from app.models.lab_order import LabOrder, LabStatus
from app.models.patient import Patient
from app.schemas.fhir_export import ExportAttempt, ExportResult
from app.services.encounter_service import EncounterNotFoundError
from app.services.lab_order_service import LabOrderNotFoundError
from app.services.patient_service import PatientNotFoundError

EXPORT_MAX_ATTEMPTS = 3


class LabResultNotAvailableError(Exception):
    """Raised when trying to export an Observation for an order with no completed result yet."""

    pass


def _submit_with_retries(
    resource_type: str, payload: dict, fail_first_n_attempts: int
) -> tuple[str, list[ExportAttempt]]:
    """
    Demonstrates SUCCESS / FAILED / RETRY concretely - see ExportRequest's
    docstring for exactly how fail_first_n_attempts drives each outcome.
    """
    client = get_health_exchange_client()
    attempts: list[ExportAttempt] = []

    for attempt in range(1, EXPORT_MAX_ATTEMPTS + 1):
        if attempt <= fail_first_n_attempts:
            attempts.append(
                ExportAttempt(
                    attempt=attempt,
                    outcome="FAILED",
                    detail=f"Forced failure for demo (attempt {attempt} of {fail_first_n_attempts})",
                )
            )
            continue

        if fail_first_n_attempts and attempt == fail_first_n_attempts + 1:
            # Guaranteed recovery attempt, bypassing the random simulator -
            # makes a "retry succeeded" demo reliably repeatable instead of
            # depending on the simulated failure_rate's luck.
            attempts.append(
                ExportAttempt(
                    attempt=attempt,
                    outcome="SUCCESS",
                    detail="Accepted by external health exchange (demo recovery)",
                )
            )
            return "SUCCESS", attempts

        try:
            client.submit_resource(resource_type, payload)
            attempts.append(
                ExportAttempt(
                    attempt=attempt, outcome="SUCCESS", detail="Accepted by external health exchange"
                )
            )
            return "SUCCESS", attempts
        except HealthExchangeError as exc:
            attempts.append(ExportAttempt(attempt=attempt, outcome="FAILED", detail=exc.reason))

    return "FAILED", attempts


# --- Patient -----------------------------------------------------------

def get_patient_fhir_resource(db: Session, patient_id: uuid.UUID) -> dict:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise PatientNotFoundError(patient_id)
    return map_patient_to_fhir(patient).model_dump(by_alias=True)


def export_patient(db: Session, patient_id: uuid.UUID, fail_first_n_attempts: int = 0) -> ExportResult:
    payload = get_patient_fhir_resource(db, patient_id)
    status, attempts = _submit_with_retries("Patient", payload, fail_first_n_attempts)
    return ExportResult(status=status, resource=payload, attempts=attempts)


# --- Encounter -----------------------------------------------------------

def _get_encounter_with_relations(db: Session, encounter_id: uuid.UUID) -> Encounter:
    encounter = db.scalar(
        select(Encounter)
        .where(Encounter.id == encounter_id)
        .options(selectinload(Encounter.patient), selectinload(Encounter.doctor))
    )
    if encounter is None:
        raise EncounterNotFoundError(encounter_id)
    return encounter


def get_encounter_fhir_resource(db: Session, encounter_id: uuid.UUID) -> dict:
    encounter = _get_encounter_with_relations(db, encounter_id)
    return map_encounter_to_fhir(encounter).model_dump(by_alias=True)


def export_encounter(
    db: Session, encounter_id: uuid.UUID, fail_first_n_attempts: int = 0
) -> ExportResult:
    payload = get_encounter_fhir_resource(db, encounter_id)
    status, attempts = _submit_with_retries("Encounter", payload, fail_first_n_attempts)
    return ExportResult(status=status, resource=payload, attempts=attempts)


# --- Lab Result / Observation --------------------------------------------

def _get_lab_order_with_relations(db: Session, lab_order_id: uuid.UUID) -> LabOrder:
    order = db.scalar(
        select(LabOrder)
        .where(LabOrder.id == lab_order_id)
        .options(
            selectinload(LabOrder.patient),
            selectinload(LabOrder.doctor),
            selectinload(LabOrder.test),
            selectinload(LabOrder.result),
        )
    )
    if order is None:
        raise LabOrderNotFoundError(lab_order_id)
    if order.status != LabStatus.COMPLETED or order.result is None:
        raise LabResultNotAvailableError()
    return order


def get_lab_result_fhir_resource(db: Session, lab_order_id: uuid.UUID) -> dict:
    order = _get_lab_order_with_relations(db, lab_order_id)
    return map_lab_result_to_fhir_observation(order).model_dump(by_alias=True)


def export_lab_result(
    db: Session, lab_order_id: uuid.UUID, fail_first_n_attempts: int = 0
) -> ExportResult:
    payload = get_lab_result_fhir_resource(db, lab_order_id)
    status, attempts = _submit_with_retries("Observation", payload, fail_first_n_attempts)
    return ExportResult(status=status, resource=payload, attempts=attempts)
