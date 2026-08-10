import uuid
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.appointment import AppointmentStatus
from app.schemas.doctor import DoctorSummary
from app.schemas.patient import PatientSummary


class AppointmentCreate(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    appointment_date: date
    appointment_time: time
    reason: str = Field(min_length=1, max_length=500)

    @field_validator("appointment_date")
    @classmethod
    def date_not_in_past(cls, value: date) -> date:
        # Deliberately NOT a DB CHECK constraint - see Part A's explanation
        # of why that would break legitimate status updates on old rows.
        if value < date.today():
            raise ValueError("appointment_date cannot be in the past")
        return value


class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus


class AppointmentRead(BaseModel):
    id: uuid.UUID
    patient: PatientSummary
    doctor: DoctorSummary
    appointment_date: date
    appointment_time: time
    reason: str
    status: AppointmentStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AppointmentPage(BaseModel):
    items: list[AppointmentRead]
    total: int
    page: int
    page_size: int
