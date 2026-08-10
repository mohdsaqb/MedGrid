import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.database.session import get_db
from app.models.encounter import EncounterStatus
from app.models.user import User, UserRole
from app.schemas.clinical_record import ClinicalRecordCreate
from app.schemas.encounter import EncounterCreate, EncounterPage, EncounterRead
from app.services.encounter_service import (
    AppointmentAlreadyHasEncounterError,
    AppointmentMismatchError,
    AppointmentNotFoundError,
    DoctorNotFoundError,
    EncounterClosedError,
    EncounterNotFoundError,
    PatientNotFoundError,
    add_clinical_record,
    close_encounter,
    create_encounter,
    get_encounter,
    list_encounters,
)

router = APIRouter(prefix="/encounters", tags=["Encounters"])

# Clinical documentation is a professional/legal act - ADMIN is
# deliberately excluded from writes here (see Part A, point 5), unlike
# every other module where ADMIN had full write access.
CAN_DOCUMENT = require_role(UserRole.DOCTOR)
CAN_READ = require_role(UserRole.ADMIN, UserRole.DOCTOR)


@router.post("", response_model=EncounterRead, status_code=status.HTTP_201_CREATED)
def create(
    data: EncounterCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_DOCUMENT),
) -> EncounterRead:
    try:
        return create_encounter(db, data)
    except PatientNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    except DoctorNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    except AppointmentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    except AppointmentMismatchError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The appointment's patient/doctor do not match this encounter",
        )
    except AppointmentAlreadyHasEncounterError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This appointment already has an encounter documented",
        )


@router.get("", response_model=EncounterPage)
def list_all(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    patient_id: uuid.UUID | None = Query(None),
    doctor_id: uuid.UUID | None = Query(None),
    status_filter: EncounterStatus | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_READ),
) -> EncounterPage:
    items, total = list_encounters(
        db,
        page=page,
        page_size=page_size,
        patient_id=patient_id,
        doctor_id=doctor_id,
        status_filter=status_filter,
    )
    return EncounterPage(items=items, total=total, page=page, page_size=page_size)


@router.get("/{encounter_id}", response_model=EncounterRead)
def get_one(
    encounter_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_READ),
) -> EncounterRead:
    try:
        return get_encounter(db, encounter_id)
    except EncounterNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")


@router.patch("/{encounter_id}/close", response_model=EncounterRead)
def close(
    encounter_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_DOCUMENT),
) -> EncounterRead:
    try:
        return close_encounter(db, encounter_id)
    except EncounterNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")
    except EncounterClosedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Encounter is already closed"
        )


@router.post(
    "/{encounter_id}/clinical-records",
    response_model=EncounterRead,
    status_code=status.HTTP_201_CREATED,
)
def add_record(
    encounter_id: uuid.UUID,
    data: ClinicalRecordCreate,
    db: Session = Depends(get_db),
    user: User = Depends(CAN_DOCUMENT),
) -> EncounterRead:
    try:
        return add_clinical_record(db, encounter_id, data, created_by_user_id=user.id)
    except EncounterNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")
    except EncounterClosedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot add a clinical record to a closed encounter",
        )
