import os
import logging
from typing import Final

class Settings:
    """
    Centralized configuration settings for the AI Engine.
    Values are loaded from the environment with sensible defaults for development.
    """
    # Sliding Window Constraints
    WINDOW_1M_SECONDS: Final[int] = int(os.getenv("WINDOW_1M_SECONDS", 60))
    WINDOW_5M_SECONDS: Final[int] = int(os.getenv("WINDOW_5M_SECONDS", 300))
    FAN_OUT_WINDOW_SECONDS: Final[int] = int(os.getenv("FAN_OUT_WINDOW_SECONDS", 180))
    
    # Heuristic Thresholds
    DORMANCY_DAYS_THRESHOLD: Final[int] = int(os.getenv("DORMANCY_DAYS_THRESHOLD", 45))
    HIGH_VALUE_THRESHOLD_INR: Final[float] = float(os.getenv("HIGH_VALUE_THRESHOLD_INR", 50000.0))
    
    # Application Config
    LOG_LEVEL: Final[str] = os.getenv("LOG_LEVEL", "INFO").upper()

settings = Settings()
