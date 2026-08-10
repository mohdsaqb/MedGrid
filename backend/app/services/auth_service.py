import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.password import hash_password, verify_password

logger = logging.getLogger(__name__)


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def register_user(db: Session, data: UserCreate) -> User:
    """
    Creates a new user. Business rules live here, not in the route:
    - email must not already be registered
    - the password is hashed before it ever touches the database
    """
    if get_user_by_email(db, data.email) is not None:
        raise EmailAlreadyRegisteredError(data.email)

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """
    Verifies credentials for login. Deliberately returns the SAME error
    for "no such user" and "wrong password" - telling an attacker which
    one it was ("that email isn't registered" vs "wrong password") leaks
    which emails have accounts, which is itself sensitive information.
    """
    # Log the EMAIL attempted, never the password - a login attempt is a
    # meaningful security-auditing event; the credential itself never is.
    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        logger.warning("Failed login attempt", extra={"email": email})
        raise InvalidCredentialsError()
    if not user.is_active:
        logger.warning("Login attempt on deactivated account", extra={"email": email})
        raise InvalidCredentialsError()

    logger.info("Successful login", extra={"email": email, "role": user.role.value})
    return user
