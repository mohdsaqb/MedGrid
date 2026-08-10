import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.lab_order import LabStatus

if TYPE_CHECKING:
    from app.models.lab_order import LabOrder


class LabResult(Base):
    """
    The outcome of a successfully processed LabOrder. UNIQUE on
    lab_order_id: a real one-to-one, only created once processing
    actually succeeds (see Part A / module intro for the failed-attempt
    handling rationale).
    """

    __tablename__ = "lab_results"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    lab_order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lab_orders.id"), unique=True, nullable=False
    )

    # String, not Numeric: many real lab results are qualitative
    # ("Positive", "Reactive", "Trace"), not just numbers.
    result: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(50))
    reference_range: Mapped[str | None] = mapped_column(String(200))

    status: Mapped[LabStatus] = mapped_column(
        Enum(LabStatus, name="lab_status"), nullable=False
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    lab_order: Mapped["LabOrder"] = relationship(back_populates="result")

    def __repr__(self) -> str:
        return f"LabResult(id={self.id!r}, lab_order_id={self.lab_order_id!r}, result={self.result!r})"
