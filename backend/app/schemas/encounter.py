import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.encounter import EncounterStatus
from app.schemas.clinical_record import ClinicalRecordRead
from app.schemas.doctor import DoctorSummary
from app.schemas.patient import PatientSummary


class EncounterCreate(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    appointment_id: uuid.UUID | None = None
    encounter_date: datetime
    diagnosis: str = Field(min_length=1, max_length=2000)
    symptoms: str = Field(min_length=1, max_length=2000)
    notes: str | None = Field(default=None, max_length=5000)

    @field_validator("encounter_date")
    @classmethod
    def encounter_date_not_in_future(cls, value: datetime) -> datetime:
        if value > datetime.now(value.tzinfo):
            raise ValueError("encounter_date cannot be in the future")
        return value


class EncounterListItem(BaseModel):
    """Lightweight shape for GET /encounters - no nested clinical records."""

    id: uuid.UUID
    patient: PatientSummary
    doctor: DoctorSummary
    appointment_id: uuid.UUID | None
    encounter_date: datetime
    diagnosis: str
    status: EncounterStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EncounterRead(BaseModel):
    """Full shape for GET /encounters/{id} and clinical history - includes
    every clinical record documented during this encounter."""

    id: uuid.UUID
    patient: PatientSummary
    doctor: DoctorSummary
    appointment_id: uuid.UUID | None
    encounter_date: datetime
    diagnosis: str
    symptoms: str
    notes: str | None
    status: EncounterStatus
    created_at: datetime
    updated_at: datetime
    clinical_records: list[ClinicalRecordRead]

    model_config = ConfigDict(from_attributes=True)


class EncounterPage(BaseModel):
    items: list[EncounterListItem]
    total: int
    page: int
    page_size: int
