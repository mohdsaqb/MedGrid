import enum
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.appointment import Appointment


class Gender(str, enum.Enum):
    """
    Administrative sex, using HL7's simple administrative-gender vocabulary
    (M/F/O/U) rather than inventing our own - relevant later when Module 9
    maps this data to FHIR Patient resources.
    """

    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class BloodGroup(str, enum.Enum):
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"


class Patient(Base):
    """
    A patient enrolled in the platform.

    Extended in Module 4 with demographic fields needed for real patient
    management. `patient_number` (formerly `mrn`) and `phone` (formerly
    `phone_number`) were renamed via migration to match this module's
    naming - see alembic/versions for the rename migration.
    """

    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # The identifier clinical/front-desk staff actually use day-to-day.
    # Server-generated (see services/patient_service.py) - never user-supplied.
    patient_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    # Identity
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[Gender | None] = mapped_column(Enum(Gender, name="patient_gender"))

    # Contact - email is optional, phone is required and indexed (front-desk
    # and billing commonly look patients up by phone).
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    address: Mapped[str | None] = mapped_column(Text)

    # Not always known at intake - only recorded once tested/confirmed.
    blood_group: Mapped[BloodGroup | None] = mapped_column(
        Enum(
            BloodGroup,
            name="patient_blood_group",
            # Without this, SQLAlchemy sends the Python member NAME
            # (e.g. "A_POSITIVE") to Postgres instead of its VALUE ("A+"),
            # which the DB enum doesn't recognize. Gender/UserRole don't
            # need this because their member names happen to equal their
            # values - BloodGroup's don't.
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        )
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("date_of_birth <= CURRENT_DATE", name="ck_patient_dob_not_future"),
    )

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="patient")

    def __repr__(self) -> str:
        return f"Patient(id={self.id!r}, patient_number={self.patient_number!r}, last_name={self.last_name!r})"
