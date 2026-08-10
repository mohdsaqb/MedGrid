import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.database.session import get_db
from app.models.user import User, UserRole
from app.schemas.fhir_export import ExportRequest, ExportResult
from app.services.encounter_service import EncounterNotFoundError
from app.services.fhir_export_service import (
    LabResultNotAvailableError,
    export_encounter,
    export_lab_result,
    export_patient,
    get_encounter_fhir_resource,
    get_lab_result_fhir_resource,
    get_patient_fhir_resource,
)
from app.services.lab_order_service import LabOrderNotFoundError
from app.services.patient_service import PatientNotFoundError

router = APIRouter(prefix="/integrations/fhir", tags=["HL7/FHIR Integration"])

# Pushing data to an external health system is an interoperability/care-
# coordination action - ADMIN for system oversight, DOCTOR for legitimate
# care-coordination needs (e.g. referring a patient elsewhere). Same
# professional-boundary reasoning as Modules 6-8; LAB_TECHNICIAN,
# BILLING_STAFF, and PATIENT excluded.
CAN_EXPORT = require_role(UserRole.ADMIN, UserRole.DOCTOR)


# ---------------------------------------------------------------------------
# Patient
# ---------------------------------------------------------------------------


@router.get("/patients/{patient_id}")
def preview_patient(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_EXPORT),
) -> dict:
    """Shows the mapped FHIR Patient JSON only - no external call made.
    Demonstrates the mapping step in isolation from transmission."""
    try:
        return get_patient_fhir_resource(db, patient_id)
    except PatientNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")


@router.post("/patients/{patient_id}/export", response_model=ExportResult)
def export_patient_route(
    patient_id: uuid.UUID,
    data: ExportRequest,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_EXPORT),
) -> ExportResult:
    try:
        result = export_patient(db, patient_id, fail_first_n_attempts=data.fail_first_n_attempts)
    except PatientNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    if result.status == "FAILED":
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=result.model_dump())
    return result


# ---------------------------------------------------------------------------
# Encounter
# ---------------------------------------------------------------------------


@router.get("/encounters/{encounter_id}")
def preview_encounter(
    encounter_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_EXPORT),
) -> dict:
    try:
        return get_encounter_fhir_resource(db, encounter_id)
    except EncounterNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")


@router.post("/encounters/{encounter_id}/export", response_model=ExportResult)
def export_encounter_route(
    encounter_id: uuid.UUID,
    data: ExportRequest,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_EXPORT),
) -> ExportResult:
    try:
        result = export_encounter(
            db, encounter_id, fail_first_n_attempts=data.fail_first_n_attempts
        )
    except EncounterNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")

    if result.status == "FAILED":
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=result.model_dump())
    return result


# ---------------------------------------------------------------------------
# Lab Result -> Observation
# ---------------------------------------------------------------------------


@router.get("/lab-results/{lab_order_id}")
def preview_lab_result(
    lab_order_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_EXPORT),
) -> dict:
    try:
        return get_lab_result_fhir_resource(db, lab_order_id)
    except LabOrderNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab order not found")
    except LabResultNotAvailableError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This lab order has no completed result to export yet",
        )


@router.post("/lab-results/{lab_order_id}/export", response_model=ExportResult)
def export_lab_result_route(
    lab_order_id: uuid.UUID,
    data: ExportRequest,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_EXPORT),
) -> ExportResult:
    try:
        result = export_lab_result(
            db, lab_order_id, fail_first_n_attempts=data.fail_first_n_attempts
        )
    except LabOrderNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab order not found")
    except LabResultNotAvailableError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This lab order has no completed result to export yet",
        )

    if result.status == "FAILED":
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=result.model_dump())
    return result
