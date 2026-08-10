import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.user import User

if TYPE_CHECKING:
    from app.models.invoice import Invoice


class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    CARD = "CARD"
    BANK_TRANSFER = "BANK_TRANSFER"


class PaymentStatus(str, enum.Enum):
    """Independent per-attempt state machine - separate from InvoiceStatus,
    which aggregates across all of an invoice's payments."""

    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Payment(Base):
    """
    One payment attempt toward an invoice. Many payments can exist per
    invoice (partial payments, retried failures) - see Part A, point 2.
    """

    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("invoices.id"), nullable=False, index=True
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, name="payment_method"), nullable=False
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        nullable=False,
        server_default=PaymentStatus.PENDING.value,
        index=True,
    )
    # Set only when payment_status becomes SUCCESS - null for PENDING/FAILED.
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Not in the literal field list - added for the same auditability reason
    # as ClinicalRecord.created_by_user_id in Module 6: money needs to be
    # traceable to exactly who recorded it, not just when.
    recorded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    invoice: Mapped["Invoice"] = relationship(back_populates="payments")
    recorded_by: Mapped[User] = relationship()

    def __repr__(self) -> str:
        return f"Payment(id={self.id!r}, invoice_id={self.invoice_id!r}, payment_status={self.payment_status!r})"
