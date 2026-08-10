from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import TokenPayload
from app.utils.jwt import decode_access_token

# Tells FastAPI (and Swagger's "Authorize" button) that tokens are obtained
# from POST /auth/login, and to expect `Authorization: Bearer <token>` on
# every other request. It does NOT do the login itself - just documents
# and extracts the header.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Runs on every protected request. Three separate failure modes are
    handled, each a 401 (unauthenticated) - not 403, because "unauthenticated"
    and "authenticated but not allowed" are different problems:
      1. token is malformed / signature invalid / expired  -> PyJWTError
      2. token is well-formed but missing our expected claims -> ValidationError
      3. token is valid but the user no longer exists / was deactivated
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        token_data = TokenPayload(**payload)
    except (PyJWTError, ValidationError):
        raise credentials_error

    user = db.get(User, token_data.sub)
    if user is None or not user.is_active:
        raise credentials_error

    return user


def require_role(*allowed_roles: UserRole):
    """
    A dependency FACTORY: require_role(UserRole.DOCTOR) returns a dependency
    function tailored to that role, so a single implementation covers every
    role-protected route rather than writing require_doctor / require_admin
    / ... five times over.
    """

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role.value}' is not permitted to access this resource",
            )
        return current_user

    return role_checker
