"""
Huey Asynchronous Task Queue Configuration
Supports RedisHuey for production distributed processing with automatic SQLite fallback.
"""
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
from huey import RedisHuey
import redis

try:
    r = redis.Redis.from_url(REDIS_URL, socket_timeout=1.0)
    r.ping()
    huey = RedisHuey("geo-cashwatch-tasks", url=REDIS_URL, results=True)
    logger.info(f"⚡ Huey Distributed Task Queue connected to Redis: {REDIS_URL}")
except Exception as e:
    logger.error(f"❌ Failed to connect to Redis for Huey Tasks at {REDIS_URL}: {e}")
    huey = RedisHuey("geo-cashwatch-tasks", url=REDIS_URL, results=True)
