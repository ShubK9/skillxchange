# backend/routes/signaling.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from websocket_manager import manager
import logging

router = APIRouter(prefix="/api/signaling", tags=["signaling"])
logger = logging.getLogger("signaling")


@router.websocket("/ws/{room_id}")
async def signaling_ws(websocket: WebSocket, room_id: str):
    """WebRTC signaling server using simple broadcast."""
    await manager.connect(room_id, websocket)
    logger.info(f"WebSocket connected → room: {room_id}")

    try:
        while True:
            data = await websocket.receive_json()

            # Broadcast to room EXCEPT sender
            await manager.broadcast(room_id, data, sender=websocket)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected → room: {room_id}")
        manager.disconnect(room_id, websocket)

    except Exception as e:
        logger.error(f"WebSocket error in room {room_id}: {e}")
        manager.disconnect(room_id, websocket)
