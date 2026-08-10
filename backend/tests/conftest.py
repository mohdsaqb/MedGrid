"""
Shared pytest fixtures. See Module 11 Part 1 for the concepts these
implement: a dedicated test database, transactional test isolation, and
reusable auth fixtures.
"""

import os

# IMPORTANT: this must run BEFORE any `app.*` import, since app/database/
# session.py creates its engine at import time from settings.database_url.
# Env vars take priority over .env in pydantic-settings, so this redirects
# the whole app - without touching the real .env file - at every test run.
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://carebridge_app:eS-eQqYHwPXP9p0eDU8Uqi0E@localhost:5432/carebridge_test",
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-use-only")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.config import settings  # noqa: E402
from app.database.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.utils.jwt import create_access_token  # noqa: E402
from app.utils.password import hash_password  # noqa: E402

engine = create_engine(settings.database_url)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def db_session():
    """
    One test = one outer transaction, rolled back at teardown, so nothing
    a test writes ever persists or leaks into another test.

    The subtlety: our service code calls db.commit() freely (that's
    correct, real behavior we want to exercise). A plain commit() on a
    session bound to an already-open connection would commit the OUTER
    transaction too, defeating the rollback. The standard SQLAlchemy fix:
    wrap the connection in a SAVEPOINT (begin_nested), and whenever that
    savepoint ends (including via a normal commit()), immediately open a
    new one - so there's always something to roll back to, while the
    outer transaction (rolled back below) is what actually undoes
    everything at the end.
    """
    connection = engine.connect()
    outer_transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, trans):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    outer_transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    """
    A FastAPI TestClient with get_db overridden to hand out THIS test's
    transactional session - the key technique for API-level tests that
    hit real routes without touching the real database.
    """

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _create_user(db_session, email: str, role: UserRole) -> User:
    user = User(
        email=email,
        hashed_password=hash_password("TestPassword123"),
        full_name=f"Test {role.value.title()}",
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(user: User) -> dict:
    token = create_access_token(user_id=user.id, role=user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_user(db_session) -> User:
    return _create_user(db_session, "admin@example.com", UserRole.ADMIN)


@pytest.fixture()
def doctor_user(db_session) -> User:
    return _create_user(db_session, "doctor@example.com", UserRole.DOCTOR)


@pytest.fixture()
def lab_tech_user(db_session) -> User:
    return _create_user(db_session, "labtech@example.com", UserRole.LAB_TECHNICIAN)


@pytest.fixture()
def billing_user(db_session) -> User:
    return _create_user(db_session, "billing@example.com", UserRole.BILLING_STAFF)


@pytest.fixture()
def patient_role_user(db_session) -> User:
    return _create_user(db_session, "patientuser@example.com", UserRole.PATIENT)


@pytest.fixture()
def admin_headers(admin_user) -> dict:
    return _auth_headers(admin_user)


@pytest.fixture()
def doctor_headers(doctor_user) -> dict:
    return _auth_headers(doctor_user)


@pytest.fixture()
def lab_tech_headers(lab_tech_user) -> dict:
    return _auth_headers(lab_tech_user)


@pytest.fixture()
def billing_headers(billing_user) -> dict:
    return _auth_headers(billing_user)


@pytest.fixture()
def patient_role_headers(patient_role_user) -> dict:
    return _auth_headers(patient_role_user)
