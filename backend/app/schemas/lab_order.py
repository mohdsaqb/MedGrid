import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.lab_order import LabStatus
from app.schemas.doctor import DoctorSummary
from app.schemas.lab_test import LabTestSummary
from app.schemas.patient import PatientSummary


class LabOrderCreate(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    test_id: uuid.UUID


class LabResultRead(BaseModel):
    id: uuid.UUID
    result: str
    unit: str | None
    reference_range: str | None
    status: LabStatus
    completed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LabOrderRead(BaseModel):
    id: uuid.UUID
    patient: PatientSummary
    doctor: DoctorSummary
    test: LabTestSummary
    status: LabStatus
    ordered_at: datetime
    result: LabResultRead | None

    model_config = ConfigDict(from_attributes=True)


class LabOrderPage(BaseModel):
    items: list[LabOrderRead]
    total: int
    page: int
    page_size: int


class ProcessLabOrderRequest(BaseModel):
    """
    simulate_failure is a TEST/DEMO HOOK ONLY - it lets us deterministically
    exercise the failure path without waiting for the random chance to hit.
    A real LIMS integration would have no such flag; this only exists
    because WE control the simulation.
    """

    simulate_failure: bool = False
