"""
WebSocket Alerts Router for Real-time Dashboard Streaming
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
from backend.app.core.connection_manager import ws_manager
from backend.app.core.stream_orchestrator import orchestrator

router = APIRouter(tags=["WebSocket"])
logger = logging.getLogger("geo_cashwatch.ws_router")

@router.websocket("/ws/alerts")
async def websocket_alerts_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for the Law Enforcement Command Center Dashboard.
    Streams real-time mule alerts, H3 geospatial cash-out hotspots, and action updates.
    """
    await ws_manager.connect(websocket)
    try:
        # Send initial state snapshot upon connection
        initial_state = orchestrator.get_initial_state()
        await ws_manager.send_personal(initial_state, websocket)

        # Keep connection open and listen for heartbeat / client commands
        while True:
            data = await websocket.receive_text()
            # Respond to ping/heartbeat if sent by client
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket client encounter error: {e}")
        ws_manager.disconnect(websocket)
