import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class UserRole(str, enum.Enum):
    """
    The fixed set of roles in the system. A Python Enum here gives us
    type-checked, autocompleted role values in code; SQLAlchemy maps it
    to a native Postgres ENUM type in the database (see the migration).
    """

    ADMIN = "ADMIN"
    DOCTOR = "DOCTOR"
    PATIENT = "PATIENT"
    LAB_TECHNICIAN = "LAB_TECHNICIAN"
    BILLING_STAFF = "BILLING_STAFF"


class User(Base):
    """
    An authentication identity - anyone who can log in, regardless of
    what kind of person they are in the clinical/business sense. That
    distinction (are they also a Patient? a Doctor?) is modeled by
    separate tables in later modules, linked back to this one.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)

    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False)

    # Lets us disable a login without deleting audit/clinical history tied
    # to this user - a real requirement for staff who leave, not a guess.
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r}, role={self.role!r})"
