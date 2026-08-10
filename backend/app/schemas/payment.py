import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.payment import PaymentMethod, PaymentStatus


class PaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0, decimal_places=2)
    payment_method: PaymentMethod


class PaymentConfirmRequest(BaseModel):
    """
    simulate_failure is a TEST/DEMO HOOK ONLY, same as Module 7's
    ProcessLabOrderRequest - it lets us deterministically exercise the
    decline path. Deliberately, there is NO field here for the caller to
    just declare a status directly (see Part A, point 5).
    """

    simulate_failure: bool = False


class PaymentRead(BaseModel):
    id: uuid.UUID
    amount: Decimal
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    recorded_by_user_id: uuid.UUID
    paid_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
