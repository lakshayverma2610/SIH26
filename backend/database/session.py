"""
Database Engine & Session Management for Geo-CashWatch
Supports PostgreSQL (Production) with transparent SQLite local fallback.
"""
import os
import logging
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from backend.database.models import Base

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_SQLITE_PATH = ROOT_DIR / "data_simulation" / "data" / "geocashwatch.db"
DEFAULT_SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")

# Normalize postgres:// to postgresql:// for SQLAlchemy 2.0
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Connection pool configurations
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_pre_ping"] = True

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
ScopedSession = scoped_session(SessionFactory)

def get_db():
    """FastAPI Dependency for database sessions."""
    db = ScopedSession()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initializes and creates all database tables if they do not exist."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(f"✅ Database tables successfully initialized using: {DATABASE_URL.split('@')[-1]}")
        return True
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False


if __name__ == "__main__":
    init_db()
    print("Database schema successfully generated.")
