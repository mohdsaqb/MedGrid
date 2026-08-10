import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.appointment import Appointment, AppointmentStatus
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.schemas.appointment import AppointmentCreate

TERMINAL_STATUSES = {AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED}


class PatientNotFoundError(Exception):
    pass


class DoctorNotFoundError(Exception):
    pass


class AppointmentNotFoundError(Exception):
    pass


class DoctorConflictError(Exception):
    """Rule 4: the doctor already has a non-cancelled appointment in this slot."""

    pass


class PatientConflictError(Exception):
    """Rule 5: the patient already has a non-cancelled appointment in this slot."""

    pass


class TerminalStatusError(Exception):
    """A COMPLETED or CANCELLED appointment's status can no longer change."""

    pass


# selectinload issues one extra batched query per relation (WHERE id IN (...))
# instead of one query PER ROW - avoids the N+1 problem when listing
# appointments, at the cost of 2 extra queries total rather than 0.
# (joinedload would do it in a single query via JOIN, but selectinload avoids
# a row-multiplying cartesian product when loading more than one relation.)
_WITH_RELATIONS = selectinload(Appointment.patient), selectinload(Appointment.doctor)


def _check_slot_conflicts(
    db: Session, *, doctor_id: uuid.UUID, patient_id: uuid.UUID, appt_date, appt_time
) -> None:
    """
    App-level pre-check purely for a clean, specific error message.
    The partial unique indexes (see Part A) are the actual guarantee -
    this check has a theoretical race condition between the SELECT and
    the INSERT, which the IntegrityError fallback in book_appointment
    catches if it ever happens.
    """
    doctor_conflict = db.scalar(
        select(Appointment.id).where(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appt_date,
            Appointment.appointment_time == appt_time,
            Appointment.status != AppointmentStatus.CANCELLED,
        )
    )
    if doctor_conflict is not None:
        raise DoctorConflictError()

    patient_conflict = db.scalar(
        select(Appointment.id).where(
            Appointment.patient_id == patient_id,
            Appointment.appointment_date == appt_date,
            Appointment.appointment_time == appt_time,
            Appointment.status != AppointmentStatus.CANCELLED,
        )
    )
    if patient_conflict is not None:
        raise PatientConflictError()


def book_appointment(db: Session, data: AppointmentCreate) -> Appointment:
    # Rules 1 & 2: patient and doctor must exist. Checked explicitly for a
    # clean 404 instead of letting a raw FK violation surface as a 500.
    if db.get(Patient, data.patient_id) is None:
        raise PatientNotFoundError(data.patient_id)
    if db.get(Doctor, data.doctor_id) is None:
        raise DoctorNotFoundError(data.doctor_id)

    # Rules 4 & 5: conflict pre-check (see docstring above on the real guarantee).
    _check_slot_conflicts(
        db,
        doctor_id=data.doctor_id,
        patient_id=data.patient_id,
        appt_date=data.appointment_date,
        appt_time=data.appointment_time,
    )

    appointment = Appointment(
        patient_id=data.patient_id,
        doctor_id=data.doctor_id,
        appointment_date=data.appointment_date,
        appointment_time=data.appointment_time,
        reason=data.reason,
    )
    db.add(appointment)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        # Fallback for the race condition the pre-check can't fully close -
        # we can't tell which partial index fired without inspecting the
        # error further, so we report the doctor-side conflict as the
        # more common real-world case (a fully precise message would
        # need to parse exc.orig, which is out of scope here).
        raise DoctorConflictError() from exc

    db.refresh(appointment)
    return db.scalar(
        select(Appointment).where(Appointment.id == appointment.id).options(*_WITH_RELATIONS)
    )


def get_appointment(db: Session, appointment_id: uuid.UUID) -> Appointment:
    appointment = db.scalar(
        select(Appointment)
        .where(Appointment.id == appointment_id)
        .options(*_WITH_RELATIONS)
    )
    if appointment is None:
        raise AppointmentNotFoundError(appointment_id)
    return appointment


def list_appointments(
    db: Session,
    *,
    page: int,
    page_size: int,
    patient_id: uuid.UUID | None,
    doctor_id: uuid.UUID | None,
    status_filter: AppointmentStatus | None,
    appointment_date: str | None,
) -> tuple[list[Appointment], int]:
    query = select(Appointment)

    if patient_id is not None:
        query = query.where(Appointment.patient_id == patient_id)
    if doctor_id is not None:
        query = query.where(Appointment.doctor_id == doctor_id)
    if status_filter is not None:
        query = query.where(Appointment.status == status_filter)
    if appointment_date is not None:
        query = query.where(Appointment.appointment_date == appointment_date)

    total = db.scalar(select(func.count()).select_from(query.subquery()))

    rows = (
        db.scalars(
            query.options(*_WITH_RELATIONS)
            .order_by(Appointment.appointment_date, Appointment.appointment_time)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .all()
    )
    return list(rows), total or 0


def update_status(
    db: Session, appointment_id: uuid.UUID, new_status: AppointmentStatus
) -> Appointment:
    appointment = get_appointment(db, appointment_id)
    if appointment.status in TERMINAL_STATUSES:
        raise TerminalStatusError()

    appointment.status = new_status
    db.commit()
    db.refresh(appointment)
    return get_appointment(db, appointment_id)
