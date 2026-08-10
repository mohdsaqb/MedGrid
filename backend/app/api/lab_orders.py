import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.database.session import get_db
from app.models.lab_order import LabStatus
from app.models.user import User, UserRole
from app.schemas.lab_order import (
    LabOrderCreate,
    LabOrderPage,
    LabOrderRead,
    ProcessLabOrderRequest,
)
from app.services.doctor_service import DoctorNotFoundError
from app.services.lab_order_service import (
    InvalidOrderStateError,
    LabOrderNotFoundError,
    LabProcessingFailedError,
    create_lab_order,
    get_lab_order,
    list_lab_orders,
    process_lab_order,
)
from app.services.lab_test_service import LabTestNotFoundError
from app.services.patient_service import PatientNotFoundError

router = APIRouter(prefix="/lab-orders", tags=["Lab Orders"])

# Ordering a test is a clinical decision - DOCTOR only, ADMIN excluded,
# same professional-boundary reasoning as Module 6's encounters.
CAN_ORDER = require_role(UserRole.DOCTOR)
# BILLING_STAFF is deliberately excluded here (unlike lab-tests catalog
# access) - seeing an order/result means seeing clinical data, not just a
# price. A proper "billing needs to know an order happened" view belongs
# to Module 8, scoped correctly there - not built here.
CAN_READ = require_role(UserRole.ADMIN, UserRole.DOCTOR, UserRole.LAB_TECHNICIAN)
# Submitting/processing a result is the lab technician's job specifically.
CAN_PROCESS = require_role(UserRole.LAB_TECHNICIAN)


@router.post("", response_model=LabOrderRead, status_code=status.HTTP_201_CREATED)
def create(
    data: LabOrderCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_ORDER),
) -> LabOrderRead:
    try:
        return create_lab_order(db, data)
    except PatientNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    except DoctorNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    except LabTestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab test not found")


@router.get("", response_model=LabOrderPage)
def list_all(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    patient_id: uuid.UUID | None = Query(None),
    doctor_id: uuid.UUID | None = Query(None),
    status_filter: LabStatus | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_READ),
) -> LabOrderPage:
    """
    One filterable endpoint covers 'list pending orders' (status=PENDING),
    'retrieve patient results' (patient_id=...), and 'retrieve doctor
    results' (doctor_id=...) - consistent with the pattern established in
    Modules 5 and 6, rather than three near-duplicate routes.
    """
    items, total = list_lab_orders(
        db,
        page=page,
        page_size=page_size,
        patient_id=patient_id,
        doctor_id=doctor_id,
        status_filter=status_filter,
    )
    return LabOrderPage(items=items, total=total, page=page, page_size=page_size)


@router.get("/{order_id}", response_model=LabOrderRead)
def get_one(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_READ),
) -> LabOrderRead:
    try:
        return get_lab_order(db, order_id)
    except LabOrderNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab order not found")


@router.post("/{order_id}/process", response_model=LabOrderRead)
def process(
    order_id: uuid.UUID,
    data: ProcessLabOrderRequest,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_PROCESS),
) -> LabOrderRead:
    try:
        return process_lab_order(db, order_id, simulate_failure=data.simulate_failure)
    except LabOrderNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab order not found")
    except InvalidOrderStateError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order must be PENDING or FAILED to be processed",
        )
    except LabProcessingFailedError as exc:
        # 502: we're a gateway to an upstream (simulated) system, and that
        # upstream system failed - not our own bug, and not the caller's
        # fault either. The order's status is already FAILED in the DB by
        # this point, so the caller can retry via the same endpoint.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LIMS processing failed: {exc.reason}",
        )
