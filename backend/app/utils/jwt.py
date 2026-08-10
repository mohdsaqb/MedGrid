from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from app.config import settings


def create_access_token(user_id: UUID, role: str) -> str:
    """
    Builds a signed JWT carrying the user's id and role, expiring after
    settings.access_token_expire_minutes. `sub` and `exp` are standard
    JWT claim names - `sub` (subject) and `exp` (expiration) are recognized
    by any JWT library, not something we invented.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """
    Verifies the signature and expiry, then returns the claims.
    Raises jwt.PyJWTError (or a subclass) if the token is invalid, expired,
    or tampered with - the caller (our FastAPI dependency) turns that into
    a 401 response.
    """
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
