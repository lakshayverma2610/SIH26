"""
WebSocket Connection Manager
Provides thread-safe and async-safe broadcast capabilities to all connected Command Center Dashboards.
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import logging

logger = logging.getLogger("geo_cashwatch.ws")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def send_personal(self, message: Dict[str, Any], websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning(f"Error sending personal message: {e}")

    async def broadcast(self, message: Dict[str, Any]):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send alert to connection: {e}")
                disconnected.append(connection)
        for dead_conn in disconnected:
            self.disconnect(dead_conn)

    @property
    def client_count(self) -> int:
        return len(self.active_connections)

ws_manager = ConnectionManager()
