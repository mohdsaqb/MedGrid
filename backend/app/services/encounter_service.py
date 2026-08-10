import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.appointment import Appointment
from app.models.clinical_record import ClinicalRecord
from app.models.doctor import Doctor
from app.models.encounter import Encounter, EncounterStatus
from app.models.patient import Patient
from app.schemas.clinical_record import ClinicalRecordCreate
from app.schemas.encounter import EncounterCreate

_WITH_RELATIONS = (
    selectinload(Encounter.patient),
    selectinload(Encounter.doctor),
    selectinload(Encounter.clinical_records),
)


class PatientNotFoundError(Exception):
    pass


class DoctorNotFoundError(Exception):
    pass


class AppointmentNotFoundError(Exception):
    pass


class AppointmentMismatchError(Exception):
    """The given appointment's patient/doctor don't match the encounter's."""

    pass


class AppointmentAlreadyHasEncounterError(Exception):
    pass


class EncounterNotFoundError(Exception):
    pass


class EncounterClosedError(Exception):
    """Raised when trying to modify a CLOSED encounter (add a record, re-close it)."""

    pass


def create_encounter(db: Session, data: EncounterCreate) -> Encounter:
    if db.get(Patient, data.patient_id) is None:
        raise PatientNotFoundError(data.patient_id)
    if db.get(Doctor, data.doctor_id) is None:
        raise DoctorNotFoundError(data.doctor_id)

    if data.appointment_id is not None:
        appointment = db.get(Appointment, data.appointment_id)
        if appointment is None:
            raise AppointmentNotFoundError(data.appointment_id)
        if appointment.patient_id != data.patient_id or appointment.doctor_id != data.doctor_id:
            raise AppointmentMismatchError()

    encounter = Encounter(
        patient_id=data.patient_id,
        doctor_id=data.doctor_id,
        appointment_id=data.appointment_id,
        encounter_date=data.encounter_date,
        diagnosis=data.diagnosis,
        symptoms=data.symptoms,
        notes=data.notes,
    )
    db.add(encounter)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        # Race-condition fallback for the appointment_id UNIQUE constraint -
        # the pre-check above can't fully close the window between check and insert.
        raise AppointmentAlreadyHasEncounterError() from exc

    db.refresh(encounter)
    return get_encounter(db, encounter.id)


def get_encounter(db: Session, encounter_id: uuid.UUID) -> Encounter:
    """
    populate_existing=True matters here specifically: within a single
    request, add_clinical_record() calls this BEFORE and AFTER inserting a
    new ClinicalRecord, on the same Session. Without it, SQLAlchemy's
    identity map returns the same Python object with its `clinical_records`
    collection already loaded from the first call (and now stale) - a
    second selectinload against an already-populated collection is a
    no-op by default. This forces a genuine re-fetch instead.
    """
    encounter = db.scalar(
        select(Encounter)
        .where(Encounter.id == encounter_id)
        .options(*_WITH_RELATIONS)
        .execution_options(populate_existing=True)
    )
    if encounter is None:
        raise EncounterNotFoundError(encounter_id)
    return encounter


def list_encounters(
    db: Session,
    *,
    page: int,
    page_size: int,
    patient_id: uuid.UUID | None,
    doctor_id: uuid.UUID | None,
    status_filter: EncounterStatus | None,
) -> tuple[list[Encounter], int]:
    query = select(Encounter)
    if patient_id is not None:
        query = query.where(Encounter.patient_id == patient_id)
    if doctor_id is not None:
        query = query.where(Encounter.doctor_id == doctor_id)
    if status_filter is not None:
        query = query.where(Encounter.status == status_filter)

    total = db.scalar(select(func.count()).select_from(query.subquery()))

    rows = db.scalars(
        query.options(selectinload(Encounter.patient), selectinload(Encounter.doctor))
        .order_by(Encounter.encounter_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(rows), total or 0


def close_encounter(db: Session, encounter_id: uuid.UUID) -> Encounter:
    encounter = get_encounter(db, encounter_id)
    if encounter.status == EncounterStatus.CLOSED:
        raise EncounterClosedError()
    encounter.status = EncounterStatus.CLOSED
    db.commit()
    return get_encounter(db, encounter_id)


def add_clinical_record(
    db: Session,
    encounter_id: uuid.UUID,
    data: ClinicalRecordCreate,
    created_by_user_id: uuid.UUID,
) -> Encounter:
    encounter = get_encounter(db, encounter_id)
    if encounter.status == EncounterStatus.CLOSED:
        # Rule from Part A: a closed encounter is frozen - append-only
        # documentation stops once the visit is formally signed off.
        raise EncounterClosedError()

    record = ClinicalRecord(
        encounter_id=encounter_id,
        record_type=data.record_type,
        description=data.description,
        created_by_user_id=created_by_user_id,
    )
    db.add(record)
    db.commit()
    return get_encounter(db, encounter_id)


def get_patient_clinical_history(db: Session, patient_id: uuid.UUID) -> list[Encounter]:
    if db.get(Patient, patient_id) is None:
        raise PatientNotFoundError(patient_id)

    rows = db.scalars(
        select(Encounter)
        .where(Encounter.patient_id == patient_id)
        .options(*_WITH_RELATIONS)
        .order_by(Encounter.encounter_date.desc())
    ).all()
    return list(rows)
