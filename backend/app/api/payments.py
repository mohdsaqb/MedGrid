import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.database.session import get_db
from app.models.user import User, UserRole
from app.schemas.invoice import InvoiceRead
from app.schemas.payment import PaymentConfirmRequest
from app.services.payment_service import (
    InvalidPaymentStateError,
    PaymentDeclinedError,
    PaymentNotFoundError,
    confirm_payment,
)

router = APIRouter(prefix="/payments", tags=["Billing"])

CAN_BILL = require_role(UserRole.ADMIN, UserRole.BILLING_STAFF)


@router.patch("/{payment_id}/status", response_model=InvoiceRead)
def update_status(
    payment_id: uuid.UUID,
    data: PaymentConfirmRequest,
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_BILL),
) -> InvoiceRead:
    """
    Despite the name (matching the requested capability), this does NOT
    let the caller set an arbitrary status - it triggers the (simulated)
    payment gateway confirmation, whose outcome determines the result.
    See Part A, point 5.
    """
    try:
        return confirm_payment(db, payment_id, simulate_failure=data.simulate_failure)
    except PaymentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    except InvalidPaymentStateError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only a PENDING payment can be confirmed",
        )
    except PaymentDeclinedError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Payment gateway declined: {exc.reason}",
        )
