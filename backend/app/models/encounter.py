import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.doctor import Doctor
from app.models.patient import Patient

if TYPE_CHECKING:
    from app.models.clinical_record import ClinicalRecord


class EncounterStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class Encounter(Base):
    """
    A single clinical interaction - the substance of a visit, as opposed
    to Appointment (the scheduling fact of it). See Part A for the full
    reasoning on why these are separate tables.
    """

    __tablename__ = "encounters"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id"), nullable=False, index=True
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("doctors.id"), nullable=False, index=True
    )
    # Optional and UNIQUE: a real one-to-one when present (Module 2's
    # Patient<->InsurancePolicy pattern, now real) - optional because a
    # walk-in encounter can exist with no prior appointment.
    appointment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("appointments.id"), unique=True, nullable=True
    )

    encounter_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    diagnosis: Mapped[str] = mapped_column(Text, nullable=False)
    symptoms: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    status: Mapped[EncounterStatus] = mapped_column(
        Enum(EncounterStatus, name="encounter_status"),
        nullable=False,
        server_default=EncounterStatus.OPEN.value,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Kept mutable (unlike ClinicalRecord) - an OPEN encounter is a working
    # document. Once CLOSED, the service layer refuses further changes.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    patient: Mapped[Patient] = relationship()
    doctor: Mapped[Doctor] = relationship()
    clinical_records: Mapped[list["ClinicalRecord"]] = relationship(
        back_populates="encounter", order_by="ClinicalRecord.created_at"
    )

    def __repr__(self) -> str:
        return f"Encounter(id={self.id!r}, patient_id={self.patient_id!r}, status={self.status!r})"
