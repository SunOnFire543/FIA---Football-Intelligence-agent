"""Database session management and connection pooling."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import settings
from app.db.models import Base

# Ensure SQLite parent directory exists if using local sqlite
db_url = settings.database_url
if db_url.startswith("sqlite"):
    # Extract file path e.g. sqlite:///./data/football_intel.db
    db_path_str = db_url.replace("sqlite:///", "")
    db_path = Path(db_path_str)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
        echo=False,
    )
else:
    engine = create_engine(db_url, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """Drop all tables (used primarily in tests)."""
    Base.metadata.drop_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency helper for yielding a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
