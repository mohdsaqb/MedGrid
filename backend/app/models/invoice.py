import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.patient import Patient

if TYPE_CHECKING:
    from app.models.payment import Payment


class InvoiceStatus(str, enum.Enum):
    """
    Derived, never set directly by a caller - recomputed from the sum of
    this invoice's SUCCESSFUL payments every time one resolves. See
    services/payment_service.py.
    """

    UNPAID = "UNPAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"


class Invoice(Base):
    """
    A billing claim against a patient. appointment_id is optional and
    deliberately NOT unique - unlike Encounter<->Appointment's real 1:1,
    a single appointment could plausibly generate more than one invoice
    (e.g. itemized separately), and an invoice might not trace to any one
    specific appointment at all (a lab-only or consolidated bill).
    """

    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id"), nullable=False, index=True
    )
    appointment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("appointments.id"), nullable=True, index=True
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, name="invoice_status"),
        nullable=False,
        server_default=InvoiceStatus.UNPAID.value,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    patient: Mapped[Patient] = relationship()
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="invoice", order_by="Payment.created_at"
    )

    def __repr__(self) -> str:
        return f"Invoice(id={self.id!r}, amount={self.amount!r}, status={self.status!r})"
