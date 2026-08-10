import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.patient import BloodGroup, Gender


class PatientBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date
    gender: Gender | None = None
    email: EmailStr | None = None
    phone: str = Field(min_length=7, max_length=20)
    address: str | None = Field(default=None, max_length=2000)
    blood_group: BloodGroup | None = None

    @field_validator("date_of_birth")
    @classmethod
    def date_of_birth_not_in_future(cls, value: date) -> date:
        # Mirrors the DB's CHECK constraint, but as a clean 422 here instead
        # of an IntegrityError surfacing as a raw 500 from the database.
        if value > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        return value


class PatientCreate(PatientBase):
    """patient_number is deliberately absent - the server generates it."""

    pass


class PatientUpdate(PatientBase):
    """
    PUT semantics: a full replacement of every editable field, per REST
    convention (PATCH would allow partial updates - we're not offering
    that in this module since it wasn't asked for).
    """

    pass


class PatientRead(PatientBase):
    id: uuid.UUID
    patient_number: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PatientPage(BaseModel):
    """Pagination envelope for GET /patients."""

    items: list[PatientRead]
    total: int
    page: int
    page_size: int


class PatientSummary(BaseModel):
    """Minimal patient info embedded in AppointmentRead - avoids forcing
    the frontend to make a second request just to show a patient's name."""

    id: uuid.UUID
    first_name: str
    last_name: str
    patient_number: str

    model_config = ConfigDict(from_attributes=True)
