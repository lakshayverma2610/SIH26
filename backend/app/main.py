"""
Geo-CashWatch FastAPI Core Gateway Entrypoint
Predictive Analytics & Real-Time Cybercrime Cash Withdrawal Forecasting (SIH 26184)
"""
import sys
import site
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# Configure System Path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import (
    APP_TITLE,
    APP_DESCRIPTION,
    APP_VERSION,
    CORS_ORIGINS,
    CORS_METHODS,
    CORS_HEADERS
)
from backend.app.core.stream_orchestrator import orchestrator
from backend.app.routers import (
    websocket_router,
    transactions_router,
    complaints_router,
    hotspots_router,
    actions_router
)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("geo_cashwatch.gateway")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Geo-CashWatch Gateway & Stream Orchestrator...")
    yield
    logger.info("Shutting down Geo-CashWatch Gateway...")

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan
)

# Enable CORS for Frontend Command Center & External Ingestion Clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=CORS_METHODS,
    allow_headers=CORS_HEADERS,
)

# Register Routers
app.include_router(websocket_router)
app.include_router(transactions_router)
app.include_router(complaints_router)
app.include_router(hotspots_router)
app.include_router(actions_router)

@app.get("/", tags=["System"])
def root():
    return {
        "service": APP_TITLE,
        "version": APP_VERSION,
        "status": "OPERATIONAL",
        "docs_url": "/docs",
        "websocket_alerts": "/ws/alerts"
    }

@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "HEALTHY",
        "service": "geo-cashwatch-backend-gateway",
        "metrics": orchestrator.get_system_metrics()
    }

@app.get("/api/v1/system/status", tags=["System"])
def system_status():
    return {
        "status": "ONLINE",
        "metrics": orchestrator.get_system_metrics()
    }
