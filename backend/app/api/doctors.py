import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.database.session import get_db
from app.models.user import User, UserRole
from app.schemas.doctor import DoctorCreate, DoctorPage, DoctorRead, DoctorUpdate
from app.services.doctor_service import (
    DoctorHasAppointmentsError,
    DoctorNotFoundError,
    DuplicateDoctorError,
    create_doctor,
    delete_doctor,
    get_doctor,
    list_doctors,
    update_doctor,
)

router = APIRouter(prefix="/doctors", tags=["Doctors"])

# Directory info is non-sensitive (unlike Patient records), so every role,
# including PATIENT, can read it - see Part B's access-control reasoning.
CAN_READ = require_role(
    UserRole.ADMIN,
    UserRole.DOCTOR,
    UserRole.LAB_TECHNICIAN,
    UserRole.BILLING_STAFF,
    UserRole.PATIENT,
)
CAN_WRITE = require_role(UserRole.ADMIN)


@router.post("", response_model=DoctorRead, status_code=status.HTTP_201_CREATED)
def create(
    data: DoctorCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_WRITE),
) -> DoctorRead:
    try:
        return create_doctor(db, data)
    except DuplicateDoctorError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A doctor with this email or license number already exists",
        )


@router.get("", response_model=DoctorPage)
def list_all(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, min_length=1, max_length=100),
    specialization: str | None = Query(None, min_length=1, max_length=100),
    department: str | None = Query(None, min_length=1, max_length=100),
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_READ),
) -> DoctorPage:
    items, total = list_doctors(
        db,
        page=page,
        page_size=page_size,
        search=search,
        specialization=specialization,
        department=department,
    )
    return DoctorPage(items=items, total=total, page=page, page_size=page_size)


@router.get("/{doctor_id}", response_model=DoctorRead)
def get_one(
    doctor_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_READ),
) -> DoctorRead:
    try:
        return get_doctor(db, doctor_id)
    except DoctorNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")


@router.put("/{doctor_id}", response_model=DoctorRead)
def update(
    doctor_id: uuid.UUID,
    data: DoctorUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_WRITE),
) -> DoctorRead:
    try:
        return update_doctor(db, doctor_id, data)
    except DoctorNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    except DuplicateDoctorError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A doctor with this email or license number already exists",
        )


@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    doctor_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_WRITE),
) -> None:
    try:
        delete_doctor(db, doctor_id)
    except DoctorNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    except DoctorHasAppointmentsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a doctor with existing appointments",
        )
