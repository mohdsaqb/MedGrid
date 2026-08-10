import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.invoice import InvoiceStatus
from app.schemas.patient import PatientSummary
from app.schemas.payment import PaymentRead


class InvoiceCreate(BaseModel):
    patient_id: uuid.UUID
    appointment_id: uuid.UUID | None = None
    amount: Decimal = Field(gt=0, decimal_places=2)


class InvoiceRead(BaseModel):
    id: uuid.UUID
    patient: PatientSummary
    appointment_id: uuid.UUID | None
    amount: Decimal
    status: InvoiceStatus
    # Computed, not stored - see invoice_service.py. Derived on every read
    # from the sum of SUCCESSFUL payments, so it can never drift out of
    # sync with the payments table the way a stored running-total could.
    amount_paid: Decimal
    balance_due: Decimal
    payments: list[PaymentRead]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoicePage(BaseModel):
    items: list[InvoiceRead]
    total: int
    page: int
    page_size: int
