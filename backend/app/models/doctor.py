import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.appointment import Appointment


class Doctor(Base):
    """
    A doctor in the platform's staff directory.

    Kept separate from `User` (login identity), same as `Patient` was in
    Module 4 - there's no user_id link yet from a logged-in DOCTOR account
    to "which Doctor row is me". That linkage is a real gap (it means a
    logged-in doctor can't yet get a personalized "my appointments" view
    without specifying their own doctor_id) - deferred to a later module
    that builds proper staff self-service, not guessed at here.
    """

    __tablename__ = "doctors"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    specialization: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    department: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    license_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="doctor")

    def __repr__(self) -> str:
        return f"Doctor(id={self.id!r}, name={self.name!r}, specialization={self.specialization!r})"
