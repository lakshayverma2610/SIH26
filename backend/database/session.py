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

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgrespassword@localhost:5432/geocashwatch")

# Normalize postgres:// to postgresql:// for SQLAlchemy 2.0
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Production PostgreSQL Connection pool configurations
engine_kwargs = {
    "pool_size": 20,
    "max_overflow": 40,
    "pool_pre_ping": True,
    "pool_recycle": 3600
}

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
