import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.database.session import get_db
from app.models.invoice import InvoiceStatus
from app.models.user import User, UserRole
from app.schemas.invoice import InvoiceCreate, InvoicePage, InvoiceRead
from app.schemas.payment import PaymentCreate
from app.services.appointment_service import AppointmentNotFoundError
from app.services.invoice_service import (
    AppointmentPatientMismatchError,
    InvoiceNotFoundError,
    create_invoice,
    get_invoice,
    list_invoices,
)
from app.services.patient_service import PatientNotFoundError
from app.services.payment_service import (
    InvoiceAlreadyPaidError,
    OverpaymentError,
    record_payment,
)

router = APIRouter(prefix="/invoices", tags=["Billing"])

# Billing is BILLING_STAFF's domain, same professional-boundary reasoning
# as Modules 6/7 - DOCTOR, LAB_TECHNICIAN, and PATIENT all excluded.
# ADMIN keeps access for administrative oversight, consistent with
# Modules 4/5's pattern for non-clinical administrative data.
CAN_BILL = require_role(UserRole.ADMIN, UserRole.BILLING_STAFF)


@router.post("", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
def create(
    data: InvoiceCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_BILL),
) -> InvoiceRead:
    try:
        return create_invoice(db, data)
    except PatientNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    except AppointmentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    except AppointmentPatientMismatchError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The appointment does not belong to this patient",
        )


@router.get("", response_model=InvoicePage)
def list_all(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    patient_id: uuid.UUID | None = Query(None),
    status_filter: InvoiceStatus | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_BILL),
) -> InvoicePage:
    """One filterable endpoint covers both the billing dashboard's general
    list and 'list patient invoices' (patient_id=...)."""
    items, total = list_invoices(
        db, page=page, page_size=page_size, patient_id=patient_id, status_filter=status_filter
    )
    return InvoicePage(items=items, total=total, page=page, page_size=page_size)


@router.get("/{invoice_id}", response_model=InvoiceRead)
def get_one(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_BILL),
) -> InvoiceRead:
    try:
        return get_invoice(db, invoice_id)
    except InvoiceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")


@router.post(
    "/{invoice_id}/payments", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED
)
def add_payment(
    invoice_id: uuid.UUID,
    data: PaymentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(CAN_BILL),
) -> InvoiceRead:
    try:
        return record_payment(db, invoice_id, data, recorded_by_user_id=user.id)
    except InvoiceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    except InvoiceAlreadyPaidError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="This invoice is already fully paid"
        )
    except OverpaymentError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment exceeds remaining balance of {exc.remaining_balance}",
        )
