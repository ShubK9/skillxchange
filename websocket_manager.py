# backend/websocket_manager.py
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("websocket")

class ConnectionManager:
    def __init__(self):
        # room_id → set of websockets
        self.rooms: Dict[str, Set[WebSocket]] = {}

    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        self.rooms[room_id].add(websocket)
        logger.info(f"Client connected to room {room_id}. Total: {len(self.rooms[room_id])}")

    def disconnect(self, room_id: str, websocket: WebSocket):
        if room_id not in self.rooms:
            return
        self.rooms[room_id].discard(websocket)
        logger.info(f"Client disconnected from room {room_id}. Remaining: {len(self.rooms[room_id])}")
        if not self.rooms[room_id]:
            del self.rooms[room_id]
            logger.info(f"Room {room_id} is now empty and removed.")

    async def send_personal(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error(f"Error sending to client: {e}")

    async def broadcast(self, room_id: str, message: dict, sender: WebSocket | None = None):
        if room_id not in self.rooms:
            return
        disconnected = []
        for ws in self.rooms[room_id]:
            if sender and ws == sender:
                continue  # don't echo back to sender if needed
            try:
                await ws.send_json(message)
            except WebSocketDisconnect:
                disconnected.append(ws)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                disconnected.append(ws)
        # Clean up disconnected
        for ws in disconnected:
            self.rooms[room_id].discard(ws)
        if not self.rooms[room_id]:
            del self.rooms[room_id]

    async def send_to_room_except(self, room_id: str, message: dict, exclude: WebSocket):
        if room_id not in self.rooms:
            return
        for ws in self.rooms[room_id]:
            if ws == exclude:
                continue
            await self.send_personal(message, ws)


# Singleton instance
manager = ConnectionManager()