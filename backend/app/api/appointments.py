import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.database.session import get_db
from app.models.appointment import AppointmentStatus
from app.models.user import User, UserRole
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentPage,
    AppointmentRead,
    AppointmentStatusUpdate,
)
from app.services.appointment_service import (
    AppointmentNotFoundError,
    DoctorConflictError,
    DoctorNotFoundError,
    PatientConflictError,
    PatientNotFoundError,
    TerminalStatusError,
    book_appointment,
    get_appointment,
    list_appointments,
    update_status,
)

router = APIRouter(prefix="/appointments", tags=["Appointments"])

# Rule 7 (unauthorized users cannot modify arbitrary appointments), enforced
# at the role level. NOTE: this does not yet scope a DOCTOR to only THEIR
# OWN appointments - that requires a User<->Doctor link that doesn't exist
# yet (same deliberate gap flagged for User<->Patient in Modules 3-4).
CAN_BOOK = require_role(UserRole.ADMIN, UserRole.DOCTOR)
CAN_READ = require_role(UserRole.ADMIN, UserRole.DOCTOR, UserRole.BILLING_STAFF)
CAN_UPDATE_STATUS = require_role(UserRole.ADMIN, UserRole.DOCTOR)


@router.post("", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED)
def book(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_BOOK),
) -> AppointmentRead:
    try:
        return book_appointment(db, data)
    except PatientNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    except DoctorNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    except DoctorConflictError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This doctor already has an appointment at that date and time",
        )
    except PatientConflictError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This patient already has an appointment at that date and time",
        )


@router.get("", response_model=AppointmentPage)
def list_all(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    patient_id: uuid.UUID | None = Query(None),
    doctor_id: uuid.UUID | None = Query(None),
    status_filter: AppointmentStatus | None = Query(None, alias="status"),
    appointment_date: date | None = Query(None),
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_READ),
) -> AppointmentPage:
    items, total = list_appointments(
        db,
        page=page,
        page_size=page_size,
        patient_id=patient_id,
        doctor_id=doctor_id,
        status_filter=status_filter,
        appointment_date=appointment_date,
    )
    return AppointmentPage(items=items, total=total, page=page, page_size=page_size)


@router.get("/{appointment_id}", response_model=AppointmentRead)
def get_one(
    appointment_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_READ),
) -> AppointmentRead:
    try:
        return get_appointment(db, appointment_id)
    except AppointmentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")


@router.patch("/{appointment_id}/status", response_model=AppointmentRead)
def change_status(
    appointment_id: uuid.UUID,
    data: AppointmentStatusUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_UPDATE_STATUS),
) -> AppointmentRead:
    try:
        return update_status(db, appointment_id, data.status)
    except AppointmentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    except TerminalStatusError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot change the status of a completed or cancelled appointment",
        )
