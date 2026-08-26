"""
Huey Asynchronous Task Queue Configuration
Supports RedisHuey for production distributed processing with automatic SQLite fallback.
"""
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_HUEY_DB = ROOT_DIR / "data_simulation" / "data" / "huey_tasks.db"
DEFAULT_HUEY_DB.parent.mkdir(parents=True, exist_ok=True)

huey = None

try:
    from huey import RedisHuey, SqliteHuey
    import redis

    # Test Redis connectivity first
    if "redis://" in REDIS_URL:
        try:
            r = redis.Redis.from_url(REDIS_URL, socket_timeout=0.5)
            r.ping()
            huey = RedisHuey("geo-cashwatch-tasks", url=REDIS_URL, results=True)
            logger.info(f"⚡ Huey Task Queue connected to Redis Master: {REDIS_URL}")
        except Exception:
            huey = SqliteHuey(filename=str(DEFAULT_HUEY_DB), results=True)
            logger.info(f"Huey Task Queue using SqliteHuey fallback: {DEFAULT_HUEY_DB}")
    else:
        huey = SqliteHuey(filename=str(DEFAULT_HUEY_DB), results=True)
        logger.info(f"Huey Task Queue using SqliteHuey: {DEFAULT_HUEY_DB}")
except Exception as e:
    try:
        from huey import SqliteHuey
        huey = SqliteHuey(filename=str(DEFAULT_HUEY_DB), results=True)
        logger.info(f"Huey initialized with SqliteHuey fallback ({e})")
    except Exception as err:
        logger.error(f"Failed to initialize Huey: {err}")
        huey = None
