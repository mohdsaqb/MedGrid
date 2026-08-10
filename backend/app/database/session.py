from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

# The engine manages a pool of actual TCP connections to Postgres.
# It's created once per process, not once per request.
engine = create_engine(settings.database_url)

# A factory for new Session objects. autoflush/autocommit are left at
# their SQLAlchemy 2.0 defaults (autocommit is gone entirely in 2.0 -
# you always commit explicitly, which keeps transaction boundaries obvious).
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency: yields one Session per request, and guarantees
    it's closed afterwards, even if the request raised an exception.

    Usage in a route (starting Module 4):
        def some_route(db: Session = Depends(get_db)): ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
