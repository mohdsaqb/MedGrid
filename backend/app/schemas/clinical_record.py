import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.clinical_record import RecordType


class ClinicalRecordCreate(BaseModel):
    record_type: RecordType
    description: str = Field(min_length=1, max_length=5000)


class ClinicalRecordRead(BaseModel):
    id: uuid.UUID
    record_type: RecordType
    description: str
    created_by_user_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
