import logging
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.payment_gateway import get_payment_gateway_client
from app.integrations.payment_gateway.exceptions import PaymentGatewayError
from app.integrations.payment_gateway.schemas import PaymentGatewayRequest
from app.models.invoice import Invoice, InvoiceStatus
from app.models.payment import Payment, PaymentStatus
from app.schemas.invoice import InvoiceRead
from app.schemas.payment import PaymentCreate
from app.services.invoice_service import InvoiceNotFoundError, get_invoice

logger = logging.getLogger(__name__)

MAX_CONFIRM_ATTEMPTS = 2
RETRY_DELAY_SECONDS = 0.3


class InvoiceAlreadyPaidError(Exception):
    pass


class OverpaymentError(Exception):
    def __init__(self, remaining_balance: Decimal) -> None:
        self.remaining_balance = remaining_balance
        super().__init__(f"Payment exceeds remaining balance of {remaining_balance}")


class PaymentNotFoundError(Exception):
    pass


class InvalidPaymentStateError(Exception):
    """Raised when confirming a payment that isn't PENDING."""

    pass


class PaymentDeclinedError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _current_balance(invoice: Invoice) -> tuple[Decimal, Decimal]:
    amount_paid = sum(
        (p.amount for p in invoice.payments if p.payment_status == PaymentStatus.SUCCESS),
        Decimal("0.00"),
    )
    return amount_paid, invoice.amount - amount_paid


def record_payment(
    db: Session, invoice_id: uuid.UUID, data: PaymentCreate, recorded_by_user_id: uuid.UUID
) -> InvoiceRead:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise InvoiceNotFoundError(invoice_id)
    if invoice.status == InvoiceStatus.PAID:
        raise InvoiceAlreadyPaidError()

    _, remaining = _current_balance(invoice)
    if data.amount > remaining:
        raise OverpaymentError(remaining)

    payment = Payment(
        invoice_id=invoice_id,
        amount=data.amount,
        payment_method=data.payment_method,
        recorded_by_user_id=recorded_by_user_id,
    )
    db.add(payment)
    db.commit()
    return get_invoice(db, invoice_id)


def confirm_payment(
    db: Session, payment_id: uuid.UUID, simulate_failure: bool = False
) -> InvoiceRead:
    """
    Confirms a PENDING payment via the (simulated) payment gateway, and -
    on success, atomically recomputes the parent invoice's status. Both
    writes happen in ONE commit (see Part A, point 4).

    Concurrency note, and a deliberate contrast with Module 7: there, we
    committed immediately after PENDING->PROCESSING specifically to avoid
    holding a database lock across a potentially long-running external
    call. Here, we hold the invoice row lock for the FULL duration of this
    call instead. That's a deliberate choice, not an oversight: a payment
    gateway confirmation is realistically a synchronous, sub-second
    operation even in production (unlike lab processing, which can take
    hours) - so the brief lock is an acceptable, simpler trade-off here.
    """
    # with_for_update() on the PAYMENT itself matters here specifically:
    # without it, two concurrent requests confirming the SAME payment could
    # both read payment_status == PENDING before either commits, and both
    # proceed to charge it through the gateway - a real double-charge, not
    # a cosmetic bug. Locking forces the second request to wait, then
    # re-read the row as it actually is (now SUCCESS/FAILED) once the first
    # commits, so it correctly rejects instead of double-confirming.
    payment = db.scalar(select(Payment).where(Payment.id == payment_id).with_for_update())
    if payment is None:
        raise PaymentNotFoundError(payment_id)
    if payment.payment_status != PaymentStatus.PENDING:
        raise InvalidPaymentStateError()

    # A SECOND lock, on the invoice: protects the aggregate recomputation
    # below from a concurrent confirmation of a SIBLING payment on the same
    # invoice reading a stale balance (Module 2's transaction lesson,
    # Module 7's concurrency lesson - now applied to money).
    invoice = db.scalar(
        select(Invoice).where(Invoice.id == payment.invoice_id).with_for_update()
    )

    request = PaymentGatewayRequest(
        payment_id=str(payment.id), amount=payment.amount, method=payment.payment_method.value
    )

    reason = "Simulated forced decline for testing"
    succeeded = False
    if not simulate_failure:
        client = get_payment_gateway_client()
        for attempt in range(1, MAX_CONFIRM_ATTEMPTS + 1):
            try:
                client.confirm_payment(request)
                succeeded = True
                break
            except PaymentGatewayError as exc:
                reason = exc.reason
                if attempt < MAX_CONFIRM_ATTEMPTS:
                    time.sleep(RETRY_DELAY_SECONDS)

    if not succeeded:
        payment.payment_status = PaymentStatus.FAILED
        db.commit()
        logger.warning(
            "Payment gateway declined payment",
            extra={"payment_id": str(payment_id), "reason": reason},
        )
        raise PaymentDeclinedError(reason)

    # Both writes below are part of the SAME transaction - one commit.
    payment.payment_status = PaymentStatus.SUCCESS
    payment.paid_at = datetime.now(timezone.utc)

    db.flush()  # so invoice.payments reflects this payment's new status below
    db.refresh(invoice)
    amount_paid, remaining = _current_balance(invoice)
    invoice.status = (
        InvoiceStatus.PAID if remaining <= 0 else InvoiceStatus.PARTIALLY_PAID
    )
    db.commit()

    if invoice.status == InvoiceStatus.PAID:
        logger.info("Invoice fully paid", extra={"invoice_id": str(invoice.id)})

    return get_invoice(db, invoice.id)
