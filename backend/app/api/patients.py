import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.database.session import get_db
from app.models.user import User, UserRole
from app.schemas.encounter import EncounterRead
from app.schemas.patient import PatientCreate, PatientPage, PatientRead, PatientUpdate
from app.services.encounter_service import PatientNotFoundError as EncounterPatientNotFoundError
from app.services.encounter_service import get_patient_clinical_history
from app.services.patient_service import (
    DuplicateEmailError,
    PatientNotFoundError,
    create_patient,
    delete_patient,
    get_patient,
    list_patients,
    update_patient,
)

router = APIRouter(prefix="/patients", tags=["Patients"])

# Reusable role groups for this module - see Part A's access-control design.
CAN_WRITE = require_role(UserRole.ADMIN, UserRole.DOCTOR)
CAN_READ = require_role(
    UserRole.ADMIN, UserRole.DOCTOR, UserRole.LAB_TECHNICIAN, UserRole.BILLING_STAFF
)
CAN_DELETE = require_role(UserRole.ADMIN)
# Clinical history is materially more sensitive than demographic data -
# a narrower role set than CAN_READ above (no LAB_TECHNICIAN/BILLING_STAFF).
CAN_READ_CLINICAL = require_role(UserRole.ADMIN, UserRole.DOCTOR)


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
def create(
    data: PatientCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_WRITE),
) -> PatientRead:
    try:
        return create_patient(db, data)
    except DuplicateEmailError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A patient with this email already exists",
        )


@router.get("", response_model=PatientPage)
def list_all(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, min_length=1, max_length=100),
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_READ),
) -> PatientPage:
    items, total = list_patients(db, page=page, page_size=page_size, search=search)
    return PatientPage(items=items, total=total, page=page, page_size=page_size)


@router.get("/{patient_id}", response_model=PatientRead)
def get_one(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_READ),
) -> PatientRead:
    try:
        return get_patient(db, patient_id)
    except PatientNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")


@router.put("/{patient_id}", response_model=PatientRead)
def update(
    patient_id: uuid.UUID,
    data: PatientUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_WRITE),
) -> PatientRead:
    try:
        return update_patient(db, patient_id, data)
    except PatientNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    except DuplicateEmailError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A patient with this email already exists",
        )


@router.get("/{patient_id}/clinical-history", response_model=list[EncounterRead])
def clinical_history(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_READ_CLINICAL),
) -> list[EncounterRead]:
    """
    The full longitudinal chart: every encounter for this patient, each
    with its complete list of clinical records nested - what a doctor
    would review before a consultation. Distinct from GET /encounters
    (a lightweight, filterable list without nested records).
    """
    try:
        return get_patient_clinical_history(db, patient_id)
    except EncounterPatientNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_DELETE),
) -> None:
    try:
        delete_patient(db, patient_id)
    except PatientNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
