"""
CARVanta – Database Connection Factory
========================================
Provides SQLAlchemy engine, session factory, and FastAPI dependency.
Supports SQLite (local), PostgreSQL (production) via DATABASE_URL env var.
"""

import os
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from db.models import Base


def _get_database_url() -> str:
    """Get database URL from environment, with sensible defaults."""
    url = os.getenv("DATABASE_URL", "")
    if not url:
        # Default to SQLite in data/ directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "data", "carvanta.db")
        url = f"sqlite:///{db_path}"
    return url


# ─── Engine ─────────────────────────────────────────────────────────────────────
DATABASE_URL = _get_database_url()
_is_sqlite = DATABASE_URL.startswith("sqlite")

_engine_kwargs = {}
if _is_sqlite:
    # SQLite-specific: enable WAL mode for better concurrency
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL: connection pooling
    _engine_kwargs["pool_size"] = 10
    _engine_kwargs["max_overflow"] = 20
    _engine_kwargs["pool_pre_ping"] = True

engine = create_engine(DATABASE_URL, echo=False, **_engine_kwargs)

# Enable WAL mode for SQLite
if _is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()


# ─── Session Factory ────────────────────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency that yields a database session.
    Automatically closes the session when the request is done.

    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """
    Context manager for non-FastAPI usage (scripts, background tasks).

    Usage:
        with get_db_session() as db:
            db.query(Biomarker).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)
    print(f"  [CARVanta DB] Initialized database: {DATABASE_URL}")
    if _is_sqlite:
        print(f"  [CARVanta DB] Mode: SQLite (local development)")
    else:
        print(f"  [CARVanta DB] Mode: PostgreSQL (production)")


def get_engine_info() -> dict:
    """Return database connection info for health checks."""
    return {
        "url": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL,
        "backend": "postgresql" if not _is_sqlite else "sqlite",
        "pool_size": _engine_kwargs.get("pool_size", "N/A"),
    }
