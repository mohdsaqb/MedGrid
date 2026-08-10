import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.user import User

if TYPE_CHECKING:
    from app.models.encounter import Encounter


class RecordType(str, enum.Enum):
    DIAGNOSIS = "DIAGNOSIS"
    PRESCRIPTION = "PRESCRIPTION"
    PROCEDURE = "PROCEDURE"
    VITALS = "VITALS"
    GENERAL_NOTE = "GENERAL_NOTE"


class ClinicalRecord(Base):
    """
    One immutable, timestamped clinical documentation entry within an
    Encounter. Deliberately has NO updated_at (see Part A) - corrections
    are made by adding a new record, never by editing an existing one.
    """

    __tablename__ = "clinical_records"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    encounter_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("encounters.id"), nullable=False, index=True
    )
    record_type: Mapped[RecordType] = mapped_column(
        Enum(RecordType, name="clinical_record_type"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Not in the literal field list - added deliberately for real
    # auditability (see Part A, point 4): every entry must be traceable
    # to exactly who wrote it, not just when.
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    encounter: Mapped["Encounter"] = relationship(back_populates="clinical_records")
    created_by: Mapped[User] = relationship()

    def __repr__(self) -> str:
        return f"ClinicalRecord(id={self.id!r}, encounter_id={self.encounter_id!r}, record_type={self.record_type!r})"
