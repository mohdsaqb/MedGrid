import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class LabTest(Base):
    """
    The test catalog - a reference/lookup entity, not an "actor" like
    Patient/Doctor (see Part A). Many LabOrders will reference one LabTest.
    """

    __tablename__ = "lab_tests"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    # A general catalog-level guideline (e.g. "4.5-11.0 x10^9/L") - distinct
    # from LabResult.reference_range, which is the range actually used for
    # one specific result (can vary by lab methodology/demographics).
    normal_range: Mapped[str | None] = mapped_column(String(200))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"LabTest(id={self.id!r}, name={self.name!r}, price={self.price!r})"
