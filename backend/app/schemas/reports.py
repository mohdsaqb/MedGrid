from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class GenderCount(BaseModel):
    gender: str
    count: int


class DepartmentPatientCount(BaseModel):
    department: str
    patient_count: int


class PatientsReport(BaseModel):
    total_patients: int
    patients_by_gender: list[GenderCount]
    patients_by_department: list[DepartmentPatientCount]


class StatusCount(BaseModel):
    status: str
    count: int


class DailyCount(BaseModel):
    day: date
    count: int


class AppointmentsReport(BaseModel):
    total_appointments: int
    appointments_by_status: list[StatusCount]
    appointments_by_day: list[DailyCount]


class PendingLabOrder(BaseModel):
    id: str
    patient_name: str
    doctor_name: str
    test_name: str
    ordered_at: str


class LabsReport(BaseModel):
    total_orders: int
    orders_by_status: list[StatusCount]
    completed_tests: int
    pending_orders: list[PendingLabOrder]


class DailyRevenue(BaseModel):
    day: date
    revenue: Decimal


class RevenueReport(BaseModel):
    total_revenue: Decimal
    total_invoiced: Decimal
    outstanding_balance: Decimal
    revenue_by_day: list[DailyRevenue]


class DoctorPerformance(BaseModel):
    id: str
    name: str
    specialization: str
    department: str
    appointment_count: int
    revenue: Decimal


class DoctorPerformanceReport(BaseModel):
    doctors: list[DoctorPerformance]
