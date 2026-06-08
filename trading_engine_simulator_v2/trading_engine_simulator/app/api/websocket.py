"""
WebSocket connection manager and endpoint.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    """Manages WebSocket connections grouped by channel."""

    def __init__(self) -> None:
        self.active_connections: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)

    def disconnect(self, websocket: WebSocket, channel: str) -> None:
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            if not self.active_connections[channel]:
                del self.active_connections[channel]

    def disconnect_all(self, websocket: WebSocket) -> None:
        for channel in list(self.active_connections.keys()):
            self.active_connections[channel].discard(websocket)
            if not self.active_connections[channel]:
                del self.active_connections[channel]

    async def broadcast(self, channel: str, data: dict[str, Any]) -> None:
        connections = self.active_connections.get(channel, set()).copy()
        message = json.dumps(data)
        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                self.disconnect(ws, channel)


async def websocket_endpoint(websocket: WebSocket, manager: ConnectionManager) -> None:
    """
    WebSocket endpoint handler.

    Clients send JSON messages to subscribe/unsubscribe:
        {"action": "subscribe", "channel": "trades:BTCUSDT"}
        {"action": "unsubscribe", "channel": "trades:BTCUSDT"}
    """
    await websocket.accept()
    subscribed_channels: set[str] = set()

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"error": "Invalid JSON"}))
                continue

            action = msg.get("action")
            channel = msg.get("channel")

            if action == "subscribe" and channel:
                await manager.connect(websocket, channel)
                subscribed_channels.add(channel)
                await websocket.send_text(json.dumps({
                    "type": "subscribed", "channel": channel
                }))

            elif action == "unsubscribe" and channel:
                manager.disconnect(websocket, channel)
                subscribed_channels.discard(channel)
                await websocket.send_text(json.dumps({
                    "type": "unsubscribed", "channel": channel
                }))

            elif action == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect_all(websocket)
