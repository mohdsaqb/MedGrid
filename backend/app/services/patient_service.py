import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate


class PatientNotFoundError(Exception):
    pass


class DuplicateEmailError(Exception):
    pass


def _next_patient_number(db: Session) -> str:
    """
    Pulls the next value from the DB sequence - atomic even if two
    registrations happen at the exact same moment, unlike computing
    MAX(patient_number) + 1 in Python (a real race condition).
    """
    next_val = db.execute(func.nextval("patient_number_seq")).scalar_one()
    return f"PT-{next_val:06d}"


def create_patient(db: Session, data: PatientCreate) -> Patient:
    patient = Patient(
        patient_number=_next_patient_number(db),
        **data.model_dump(),
    )
    db.add(patient)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        # The only realistic unique-constraint collision on user input here
        # is email (patient_number came from our own sequence).
        raise DuplicateEmailError(data.email) from exc
    db.refresh(patient)
    return patient


def get_patient(db: Session, patient_id: uuid.UUID) -> Patient:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise PatientNotFoundError(patient_id)
    return patient


def list_patients(
    db: Session, *, page: int, page_size: int, search: str | None
) -> tuple[list[Patient], int]:
    """
    Returns (rows for this page, total matching rows) so the caller can
    build a pagination envelope without a second round trip for the count.
    """
    query = select(Patient)

    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                Patient.first_name.ilike(pattern),
                Patient.last_name.ilike(pattern),
                Patient.patient_number.ilike(pattern),
                Patient.phone.ilike(pattern),
            )
        )

    total = db.scalar(select(func.count()).select_from(query.subquery()))

    rows = (
        db.scalars(
            query.order_by(Patient.last_name)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .all()
    )
    return list(rows), total or 0


def update_patient(db: Session, patient_id: uuid.UUID, data: PatientUpdate) -> Patient:
    patient = get_patient(db, patient_id)
    for field, value in data.model_dump().items():
        setattr(patient, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateEmailError(data.email) from exc
    db.refresh(patient)
    return patient


def delete_patient(db: Session, patient_id: uuid.UUID) -> None:
    patient = get_patient(db, patient_id)
    db.delete(patient)
    db.commit()
