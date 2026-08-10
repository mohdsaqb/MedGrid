import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class LabTestCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    price: Decimal = Field(gt=0, decimal_places=2)
    normal_range: str | None = Field(default=None, max_length=200)


class LabTestUpdate(LabTestCreate):
    pass


class LabTestRead(LabTestCreate):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LabTestSummary(BaseModel):
    """Embedded in LabOrderRead - avoids a second round trip for test details."""

    id: uuid.UUID
    name: str
    price: Decimal

    model_config = ConfigDict(from_attributes=True)


class LabTestPage(BaseModel):
    items: list[LabTestRead]
    total: int
    page: int
    page_size: int
