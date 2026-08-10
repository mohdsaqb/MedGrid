import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class DoctorBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    specialization: str = Field(min_length=1, max_length=100)
    department: str = Field(min_length=1, max_length=100)
    license_number: str = Field(min_length=1, max_length=50)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=20)


class DoctorCreate(DoctorBase):
    pass


class DoctorUpdate(DoctorBase):
    pass


class DoctorRead(DoctorBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DoctorSummary(BaseModel):
    """Minimal doctor info embedded in AppointmentRead - avoids forcing
    the frontend to make a second request just to show a doctor's name."""

    id: uuid.UUID
    name: str
    specialization: str

    model_config = ConfigDict(from_attributes=True)


class DoctorPage(BaseModel):
    items: list[DoctorRead]
    total: int
    page: int
    page_size: int
