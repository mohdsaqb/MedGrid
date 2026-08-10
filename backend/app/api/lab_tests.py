import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.database.session import get_db
from app.models.user import User, UserRole
from app.schemas.lab_test import LabTestCreate, LabTestPage, LabTestRead, LabTestUpdate
from app.services.lab_test_service import (
    DuplicateLabTestError,
    LabTestInUseError,
    LabTestNotFoundError,
    create_lab_test,
    delete_lab_test,
    get_lab_test,
    list_lab_tests,
    update_lab_test,
)

router = APIRouter(prefix="/lab-tests", tags=["Lab Tests"])

# Catalog data (name + price) is non-sensitive, like the Doctor directory -
# open to every role, including PATIENT.
CAN_READ = require_role(
    UserRole.ADMIN,
    UserRole.DOCTOR,
    UserRole.LAB_TECHNICIAN,
    UserRole.BILLING_STAFF,
    UserRole.PATIENT,
)
CAN_WRITE = require_role(UserRole.ADMIN)


@router.post("", response_model=LabTestRead, status_code=status.HTTP_201_CREATED)
def create(
    data: LabTestCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_WRITE),
) -> LabTestRead:
    try:
        return create_lab_test(db, data)
    except DuplicateLabTestError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A lab test with this name already exists",
        )


@router.get("", response_model=LabTestPage)
def list_all(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_READ),
) -> LabTestPage:
    items, total = list_lab_tests(db, page=page, page_size=page_size)
    return LabTestPage(items=items, total=total, page=page, page_size=page_size)


@router.get("/{test_id}", response_model=LabTestRead)
def get_one(
    test_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_READ),
) -> LabTestRead:
    try:
        return get_lab_test(db, test_id)
    except LabTestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab test not found")


@router.put("/{test_id}", response_model=LabTestRead)
def update(
    test_id: uuid.UUID,
    data: LabTestUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_WRITE),
) -> LabTestRead:
    try:
        return update_lab_test(db, test_id, data)
    except LabTestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab test not found")
    except DuplicateLabTestError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A lab test with this name already exists",
        )


@router.delete("/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    test_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_WRITE),
) -> None:
    try:
        delete_lab_test(db, test_id)
    except LabTestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab test not found")
    except LabTestInUseError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a lab test that has existing orders",
        )
