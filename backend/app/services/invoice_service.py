import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.appointment import Appointment
from app.models.invoice import Invoice, InvoiceStatus
from app.models.patient import Patient
from app.models.payment import Payment, PaymentStatus
from app.schemas.invoice import InvoiceCreate, InvoiceRead
from app.schemas.payment import PaymentRead
from app.services.appointment_service import AppointmentNotFoundError
from app.services.patient_service import PatientNotFoundError

_WITH_RELATIONS = (selectinload(Invoice.patient), selectinload(Invoice.payments))


class InvoiceNotFoundError(Exception):
    pass


class AppointmentPatientMismatchError(Exception):
    """The given appointment doesn't belong to this invoice's patient."""

    pass


def _to_read(invoice: Invoice) -> InvoiceRead:
    """
    Builds the response explicitly rather than via from_attributes, because
    amount_paid/balance_due are computed, not columns on the model - see
    InvoiceRead's docstring on why they're derived instead of stored.
    """
    amount_paid: Decimal = sum(
        (p.amount for p in invoice.payments if p.payment_status == PaymentStatus.SUCCESS),
        Decimal("0.00"),
    )
    return InvoiceRead(
        id=invoice.id,
        patient=invoice.patient,
        appointment_id=invoice.appointment_id,
        amount=invoice.amount,
        status=invoice.status,
        amount_paid=amount_paid,
        balance_due=invoice.amount - amount_paid,
        payments=[PaymentRead.model_validate(p) for p in invoice.payments],
        created_at=invoice.created_at,
        updated_at=invoice.updated_at,
    )


def create_invoice(db: Session, data: InvoiceCreate) -> InvoiceRead:
    if db.get(Patient, data.patient_id) is None:
        raise PatientNotFoundError(data.patient_id)

    if data.appointment_id is not None:
        appointment = db.get(Appointment, data.appointment_id)
        if appointment is None:
            raise AppointmentNotFoundError(data.appointment_id)
        if appointment.patient_id != data.patient_id:
            raise AppointmentPatientMismatchError()

    invoice = Invoice(
        patient_id=data.patient_id,
        appointment_id=data.appointment_id,
        amount=data.amount,
    )
    db.add(invoice)
    db.commit()
    return get_invoice(db, invoice.id)


def get_invoice(db: Session, invoice_id: uuid.UUID) -> InvoiceRead:
    invoice = db.scalar(
        select(Invoice)
        .where(Invoice.id == invoice_id)
        .options(*_WITH_RELATIONS)
        .execution_options(populate_existing=True)
    )
    if invoice is None:
        raise InvoiceNotFoundError(invoice_id)
    return _to_read(invoice)


def list_invoices(
    db: Session,
    *,
    page: int,
    page_size: int,
    patient_id: uuid.UUID | None,
    status_filter: InvoiceStatus | None,
) -> tuple[list[InvoiceRead], int]:
    query = select(Invoice)
    if patient_id is not None:
        query = query.where(Invoice.patient_id == patient_id)
    if status_filter is not None:
        query = query.where(Invoice.status == status_filter)

    total = db.scalar(select(func.count()).select_from(query.subquery()))

    rows = db.scalars(
        query.options(*_WITH_RELATIONS)
        .order_by(Invoice.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return [_to_read(row) for row in rows], total or 0
