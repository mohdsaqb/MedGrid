"""
Importing every model here means anything that imports `app.models`
(most importantly alembic/env.py) sees the full picture on Base.metadata,
without needing to remember to import each new model file by hand.
"""

from app.models.patient import Patient
from app.models.user import User, UserRole
from app.models.doctor import Doctor
from app.models.appointment import Appointment, AppointmentStatus
from app.models.encounter import Encounter, EncounterStatus
from app.models.clinical_record import ClinicalRecord, RecordType
from app.models.lab_test import LabTest
from app.models.lab_order import LabOrder, LabStatus
from app.models.lab_result import LabResult

__all__ = [
    "Patient",
    "User",
    "UserRole",
    "Doctor",
    "Appointment",
    "AppointmentStatus",
    "Encounter",
    "EncounterStatus",
    "ClinicalRecord",
    "RecordType",
    "LabTest",
    "LabOrder",
    "LabStatus",
    "LabResult",
]
