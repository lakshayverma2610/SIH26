"""
Application Configuration and Settings
"""
from pathlib import Path
from typing import List

# Project Root Directory
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = Path(__file__).resolve().parent.parent

# Application Info
APP_TITLE = "Geo-CashWatch API Gateway"
APP_DESCRIPTION = "High-Throughput Stream Ingestion & Cybercrime Cash Withdrawal Forecasting (SIH 26184)"
APP_VERSION = "1.0.0"

# CORS Configuration
CORS_ORIGINS: List[str] = ["*"]
CORS_METHODS: List[str] = ["*"]
CORS_HEADERS: List[str] = ["*"]

# Sliding Window & Buffer Limits
MAX_RECENT_TRANSACTIONS = 100
MAX_FLAGGED_EVENTS_BUFFER = 50
HOTSPOT_RECALC_INTERVAL_SECS = 2.0

# Mock Data Paths (if available)
ATMS_DATA_PATH = ROOT_DIR / "mock_data" / "data" / "atms.json"
ACCOUNTS_DATA_PATH = ROOT_DIR / "mock_data" / "data" / "accounts.json"
