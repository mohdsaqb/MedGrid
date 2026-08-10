import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.doctor import Doctor
from app.schemas.doctor import DoctorCreate, DoctorUpdate


class DoctorNotFoundError(Exception):
    pass


class DuplicateDoctorError(Exception):
    """Raised for a collision on either license_number or email."""

    pass


class DoctorHasAppointmentsError(Exception):
    """Raised when deletion is blocked by the FK RESTRICT from appointments."""

    pass


def create_doctor(db: Session, data: DoctorCreate) -> Doctor:
    doctor = Doctor(**data.model_dump())
    db.add(doctor)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateDoctorError() from exc
    db.refresh(doctor)
    return doctor


def get_doctor(db: Session, doctor_id: uuid.UUID) -> Doctor:
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        raise DoctorNotFoundError(doctor_id)
    return doctor


def list_doctors(
    db: Session,
    *,
    page: int,
    page_size: int,
    search: str | None,
    specialization: str | None,
    department: str | None,
) -> tuple[list[Doctor], int]:
    query = select(Doctor)

    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(Doctor.name.ilike(pattern), Doctor.license_number.ilike(pattern))
        )
    if specialization:
        query = query.where(Doctor.specialization.ilike(specialization))
    if department:
        query = query.where(Doctor.department.ilike(department))

    total = db.scalar(select(func.count()).select_from(query.subquery()))

    rows = db.scalars(
        query.order_by(Doctor.name).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return list(rows), total or 0


def update_doctor(db: Session, doctor_id: uuid.UUID, data: DoctorUpdate) -> Doctor:
    doctor = get_doctor(db, doctor_id)
    for field, value in data.model_dump().items():
        setattr(doctor, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateDoctorError() from exc
    db.refresh(doctor)
    return doctor


def delete_doctor(db: Session, doctor_id: uuid.UUID) -> None:
    doctor = get_doctor(db, doctor_id)
    db.delete(doctor)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        # The appointments.doctor_id FK has no ON DELETE CASCADE - by design,
        # so clinical history can't silently disappear (see Module 2/4).
        raise DoctorHasAppointmentsError() from exc
