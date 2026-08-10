import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    """
    Input shape for POST /auth/register.

    SECURITY NOTE (deliberate, temporary simplification): allowing the
    caller to pick any `role`, including ADMIN, is NOT how a real system
    works. In production, self-service registration would only ever be
    allowed to create PATIENT accounts; staff accounts (DOCTOR, ADMIN,
    LAB_TECHNICIAN, BILLING_STAFF) would be created by an existing ADMIN
    through a separate, protected endpoint - which doesn't exist yet
    (that's admin user-management, a later module). We're allowing open
    role selection here ONLY so we can teach and test all 5 roles without
    building that admin flow prematurely. This must be locked down before
    this project is ever exposed publicly.
    """

    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=200)
    role: UserRole


class UserRead(BaseModel):
    """Output shape - notice hashed_password is never included here."""

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    # Lets Pydantic build this schema directly from a SQLAlchemy User
    # instance (model attributes), not just from a dict.
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Shape of the decoded JWT claims we actually rely on."""

    sub: uuid.UUID
    role: UserRole
