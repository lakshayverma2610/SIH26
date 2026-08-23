from .websocket import router as websocket_router
from .transactions import router as transactions_router
from .complaints import router as complaints_router
from .hotspots import router as hotspots_router
from .actions import router as actions_router

__all__ = [
    "websocket_router",
    "transactions_router",
    "complaints_router",
    "hotspots_router",
    "actions_router"
]
