"""
Database module for EMBM-J DS Multi-Agent System.

PHASE 5 ENHANCEMENT: Persistent storage with SQLAlchemy.

Provides:
- Database connection management
- Session creation and cleanup
- Schema initialization
- Migration support
"""

import os
from pathlib import Path
from typing import Generator, Optional
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import structlog

from config import get_config
from database.models import Base


logger = structlog.get_logger(__name__)


# Global engine and session factory
_engine = None
_SessionFactory = None


def get_database_url() -> str:
    """
    Get database URL from config or environment.

    Returns:
        Database connection URL
    """
    config = get_config()

    # Check environment variable first
    db_url = os.getenv("EMBM_DATABASE_URL")

    if db_url:
        return db_url

    # Use config
    if not config.database.enabled:
        # Default to SQLite in-memory for development
        logger.warning(
            "database_disabled_in_config",
            message="Using in-memory SQLite database"
        )
        return "sqlite:///:memory:"

    if config.database.type == "sqlite":
        # SQLite file database
        db_dir = Path(__file__).parent.parent / "data"
        db_dir.mkdir(exist_ok=True)

        db_file = db_dir / "embm.db"
        return f"sqlite:///{db_file}"

    elif config.database.type == "postgresql":
        # PostgreSQL database
        user = os.getenv("EMBM_DB_USER", "embm")
        password = os.getenv("EMBM_DB_PASSWORD", "")
        host = config.database.host
        port = config.database.port
        name = config.database.name

        if not password:
            logger.warning(
                "postgresql_no_password",
                message="PostgreSQL password not set in environment"
            )

        return f"postgresql://{user}:{password}@{host}:{port}/{name}"

    else:
        raise ValueError(f"Unsupported database type: {config.database.type}")


def init_database(database_url: Optional[str] = None, echo: bool = False) -> None:
    """
    Initialize database connection and create tables.

    Args:
        database_url: Database connection URL (defaults to config)
        echo: Whether to echo SQL statements (for debugging)
    """
    global _engine, _SessionFactory

    if _engine is not None:
        logger.warning("database_already_initialized")
        return

    # Get database URL
    if database_url is None:
        database_url = get_database_url()

    logger.info(
        "database_initializing",
        url=database_url.split("@")[-1] if "@" in database_url else database_url  # Hide password
    )

    # Create engine
    if database_url.startswith("sqlite:///:memory:"):
        # In-memory SQLite needs special handling for thread safety
        _engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=echo
        )
    else:
        _engine = create_engine(
            database_url,
            echo=echo,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600   # Recycle connections after 1 hour
        )

    # Enable foreign keys for SQLite
    if database_url.startswith("sqlite"):
        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    # Create session factory
    _SessionFactory = sessionmaker(bind=_engine, expire_on_commit=False)

    # Create all tables
    Base.metadata.create_all(_engine)

    logger.info(
        "database_initialized",
        tables=len(Base.metadata.tables)
    )


def get_session() -> Session:
    """
    Get a new database session.

    Returns:
        SQLAlchemy session

    Raises:
        RuntimeError: If database not initialized
    """
    if _SessionFactory is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")

    return _SessionFactory()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Provide a transactional scope for database operations.

    Usage:
        with session_scope() as session:
            session.add(obj)
            # Changes committed automatically on successful exit
            # Rolled back on exception

    Yields:
        Database session
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(
            "database_transaction_error",
            error=str(e),
            error_type=type(e).__name__
        )
        raise
    finally:
        session.close()


def drop_all_tables() -> None:
    """
    Drop all database tables.

    WARNING: This will delete all data!
    Only use in development/testing.
    """
    if _engine is None:
        raise RuntimeError("Database not initialized")

    logger.warning("database_dropping_all_tables")
    Base.metadata.drop_all(_engine)
    logger.info("database_tables_dropped")


def close_database() -> None:
    """Close database connection and cleanup."""
    global _engine, _SessionFactory

    if _engine is not None:
        _engine.dispose()
        _engine = None
        _SessionFactory = None

        logger.info("database_closed")


# Export commonly used items
__all__ = [
    "init_database",
    "get_session",
    "session_scope",
    "drop_all_tables",
    "close_database",
    "Base",
]
