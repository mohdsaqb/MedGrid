import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.lab_test import LabTest
from app.schemas.lab_test import LabTestCreate, LabTestUpdate


class LabTestNotFoundError(Exception):
    pass


class DuplicateLabTestError(Exception):
    pass


class LabTestInUseError(Exception):
    """Raised when deletion is blocked by existing lab_orders referencing this test."""

    pass


def create_lab_test(db: Session, data: LabTestCreate) -> LabTest:
    test = LabTest(**data.model_dump())
    db.add(test)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateLabTestError() from exc
    db.refresh(test)
    return test


def get_lab_test(db: Session, test_id: uuid.UUID) -> LabTest:
    test = db.get(LabTest, test_id)
    if test is None:
        raise LabTestNotFoundError(test_id)
    return test


def list_lab_tests(db: Session, *, page: int, page_size: int) -> tuple[list[LabTest], int]:
    total = db.scalar(select(func.count()).select_from(LabTest))
    rows = db.scalars(
        select(LabTest).order_by(LabTest.name).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return list(rows), total or 0


def update_lab_test(db: Session, test_id: uuid.UUID, data: LabTestUpdate) -> LabTest:
    test = get_lab_test(db, test_id)
    for field, value in data.model_dump().items():
        setattr(test, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateLabTestError() from exc
    db.refresh(test)
    return test


def delete_lab_test(db: Session, test_id: uuid.UUID) -> None:
    test = get_lab_test(db, test_id)
    db.delete(test)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise LabTestInUseError() from exc
