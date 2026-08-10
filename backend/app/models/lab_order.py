import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.doctor import Doctor
from app.models.lab_test import LabTest
from app.models.patient import Patient

if TYPE_CHECKING:
    from app.models.lab_result import LabResult


class LabStatus(str, enum.Enum):
    """
    Shared status vocabulary for both LabOrder and LabResult (see the
    model docstrings for why LabResult practically only ever uses
    COMPLETED). One enum type, reused, rather than two near-identical ones.
    """

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class LabOrder(Base):
    """A doctor's request for a patient to have a specific lab test performed."""

    __tablename__ = "lab_orders"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id"), nullable=False, index=True
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("doctors.id"), nullable=False, index=True
    )
    test_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lab_tests.id"), nullable=False, index=True
    )

    status: Mapped[LabStatus] = mapped_column(
        Enum(LabStatus, name="lab_status"),
        nullable=False,
        server_default=LabStatus.PENDING.value,
        index=True,
    )
    ordered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    patient: Mapped[Patient] = relationship()
    doctor: Mapped[Doctor] = relationship()
    test: Mapped[LabTest] = relationship()
    result: Mapped["LabResult | None"] = relationship(back_populates="lab_order")

    def __repr__(self) -> str:
        return f"LabOrder(id={self.id!r}, status={self.status!r})"
