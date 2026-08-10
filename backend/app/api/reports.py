from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.database.session import get_db
from app.models.user import User, UserRole
from app.schemas.reports import (
    AppointmentsReport,
    DoctorPerformanceReport,
    LabsReport,
    PatientsReport,
    RevenueReport,
)
from app.services.reporting_service import (
    get_appointments_report,
    get_doctor_performance_report,
    get_labs_report,
    get_patients_report,
    get_revenue_report,
)

router = APIRouter(prefix="/reports", tags=["Reporting & Analytics"])

# Cross-patient, cross-doctor business analytics is an administrative/
# oversight concern by nature, distinct from any one doctor's or billing
# clerk's own scoped work - ADMIN only. (A more granular system might let
# BILLING_STAFF see just /reports/revenue; bundling everything behind
# ADMIN keeps this module's scope clean - a documented simplification,
# not an oversight.)
CAN_VIEW_REPORTS = require_role(UserRole.ADMIN)


@router.get("/patients", response_model=PatientsReport)
def patients_report(
    db: Session = Depends(get_db), _user: User = Depends(CAN_VIEW_REPORTS)
) -> PatientsReport:
    return PatientsReport(**get_patients_report(db))


@router.get("/appointments", response_model=AppointmentsReport)
def appointments_report(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_VIEW_REPORTS),
) -> AppointmentsReport:
    return AppointmentsReport(**get_appointments_report(db, days=days))


@router.get("/labs", response_model=LabsReport)
def labs_report(
    db: Session = Depends(get_db), _user: User = Depends(CAN_VIEW_REPORTS)
) -> LabsReport:
    return LabsReport(**get_labs_report(db))


@router.get("/revenue", response_model=RevenueReport)
def revenue_report(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    _user: User = Depends(CAN_VIEW_REPORTS),
) -> RevenueReport:
    return RevenueReport(**get_revenue_report(db, days=days))


@router.get("/doctor-performance", response_model=DoctorPerformanceReport)
def doctor_performance_report(
    db: Session = Depends(get_db), _user: User = Depends(CAN_VIEW_REPORTS)
) -> DoctorPerformanceReport:
    return DoctorPerformanceReport(**get_doctor_performance_report(db))
