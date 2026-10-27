
import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

load_dotenv()

logger = logging.getLogger("recruitment_system.database")

# Environment configuration
DEFAULT_SQLITE_URL = "sqlite:///./data/recruitment.db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL).strip()

if not DATABASE_URL:
    raise ValueError("DATABASE_URL must not be empty.")

# Ensure the default SQLite database directory exists.
if DATABASE_URL == DEFAULT_SQLITE_URL:
    Path("./data").mkdir(parents=True, exist_ok=True)

# Configure engine arguments based on the database dialect.
engine_kwargs = {
    "echo": os.getenv("SQLALCHEMY_ECHO", "false").lower()
    in {"1", "true", "yes"},
    "pool_pre_ping": True,
}

if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Pool settings for server-based databases.
    engine_kwargs.update(
        {
            "pool_recycle": 3600,
            "pool_size": 10,
            "max_overflow": 20,
        }
    )

engine: Engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Provide a database session for FastAPI and close it afterward."""
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Provide a transactional database session.

    Commits when the block succeeds and rolls back if an exception occurs.
    """
    db = SessionLocal()

    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Database transaction failed; changes rolled back.")
        raise
    finally:
        db.close()


def init_db(target_engine: Optional[Engine] = None) -> None:
    """Create all tables registered with Base metadata."""
    eng = target_engine or engine
    Base.metadata.create_all(bind=eng)
    logger.info("Database schema created or verified successfully.")


def reset_db_for_test(target_engine: Optional[Engine] = None) -> None:
    """
    Drop and recreate all registered tables.

    Use only with an isolated test database. This operation deletes existing
    tables and their data.
    """
    eng = target_engine or engine
    Base.metadata.drop_all(bind=eng)
    Base.metadata.create_all(bind=eng)
    logger.info("Test database schema reset successfully.")
