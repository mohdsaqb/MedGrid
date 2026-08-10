from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    The base class every SQLAlchemy model inherits from.

    Kept in its own file (not session.py) so models can import it without
    also pulling in the engine/session machinery - avoids circular imports
    once Alembic and models both need to reference Base.
    """

    pass
