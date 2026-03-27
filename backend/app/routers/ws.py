from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ws_manager import manager
from app.scheduler import get_all_cached

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send current cached state on connect
        cached = get_all_cached()
        for data in cached.values():
            await websocket.send_json(data)

        # Keep connection alive; client doesn't need to send anything
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
