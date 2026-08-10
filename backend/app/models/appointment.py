import enum
import uuid
from datetime import date, datetime, time

from sqlalchemy import (
    DateTime,
    Date,
    Enum,
    ForeignKey,
    Index,
    String,
    Time,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.doctor import Doctor
from app.models.patient import Patient


class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class Appointment(Base):
    """
    A booked meeting between one Patient and one Doctor at a specific
    date/time. See Part A's design note: this is two converging
    one-to-many relationships with its own attributes, not a bare
    many-to-many junction table.
    """

    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Postgres does NOT auto-index foreign keys (unlike MySQL) - both are
    # indexed explicitly since "all appointments for this patient/doctor"
    # is a query we run constantly.
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id"), nullable=False, index=True
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("doctors.id"), nullable=False, index=True
    )

    appointment_date: Mapped[date] = mapped_column(Date, nullable=False)
    appointment_time: Mapped[time] = mapped_column(Time, nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)

    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, name="appointment_status"),
        nullable=False,
        server_default=AppointmentStatus.SCHEDULED.value,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    patient: Mapped[Patient] = relationship(back_populates="appointments")
    doctor: Mapped[Doctor] = relationship(back_populates="appointments")

    __table_args__ = (
        # Atomic conflict prevention (see Part A) - the app also checks
        # this proactively for a clean error message, but THESE indexes
        # are what actually guarantee no race condition can double-book
        # a doctor or a patient, regardless of application-level timing.
        Index(
            "ux_appointments_doctor_slot",
            "doctor_id",
            "appointment_date",
            "appointment_time",
            unique=True,
            postgresql_where=text("status != 'CANCELLED'"),
        ),
        Index(
            "ux_appointments_patient_slot",
            "patient_id",
            "appointment_date",
            "appointment_time",
            unique=True,
            postgresql_where=text("status != 'CANCELLED'"),
        ),
    )

    def __repr__(self) -> str:
        return (
            f"Appointment(id={self.id!r}, patient_id={self.patient_id!r}, "
            f"doctor_id={self.doctor_id!r}, status={self.status!r})"
        )
