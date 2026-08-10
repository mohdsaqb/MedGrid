"""
TEMPORARY test-only endpoints for Module 3.

These exist purely to demonstrate role-based access control end-to-end
before the real Patient/Doctor/Lab/Billing/Admin modules exist. Each one
should be deleted once its corresponding real module (4-8) adds actual
business endpoints protected the same way.
"""

from fastapi import APIRouter, Depends

from app.api.deps import require_role
from app.models.user import User, UserRole

router = APIRouter(prefix="/test", tags=["Role Test (temporary)"])


@router.get("/patient")
def patient_only(user: User = Depends(require_role(UserRole.PATIENT))) -> dict[str, str]:
    return {"message": f"Hello {user.full_name}, you have PATIENT access."}


@router.get("/doctor")
def doctor_only(user: User = Depends(require_role(UserRole.DOCTOR))) -> dict[str, str]:
    return {"message": f"Hello {user.full_name}, you have DOCTOR access."}


@router.get("/lab")
def lab_only(user: User = Depends(require_role(UserRole.LAB_TECHNICIAN))) -> dict[str, str]:
    return {"message": f"Hello {user.full_name}, you have LAB_TECHNICIAN access."}


@router.get("/billing")
def billing_only(user: User = Depends(require_role(UserRole.BILLING_STAFF))) -> dict[str, str]:
    return {"message": f"Hello {user.full_name}, you have BILLING_STAFF access."}


@router.get("/admin")
def admin_only(user: User = Depends(require_role(UserRole.ADMIN))) -> dict[str, str]:
    return {"message": f"Hello {user.full_name}, you have ADMIN access."}
