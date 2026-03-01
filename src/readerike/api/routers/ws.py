"""WebSocket router — real-time job progress events."""

import asyncio
import logging
from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()

# job_id → list of active WebSocket connections
_connections: dict[str, list[WebSocket]] = defaultdict(list)


async def broadcast(job_id: str, payload: dict[str, object]) -> None:
    """Send *payload* as JSON to all subscribers of *job_id*."""
    dead: list[WebSocket] = []
    for ws in list(_connections[job_id]):
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _connections[job_id].remove(ws)


@router.websocket("/jobs/{job_id}/ws")
async def job_progress_ws(job_id: str, websocket: WebSocket) -> None:
    """Subscribe to live progress events for *job_id*."""
    await websocket.accept()
    _connections[job_id].append(websocket)
    logger.debug("WS client connected for job %s", job_id)
    try:
        while True:
            await asyncio.sleep(30)
            await websocket.send_json({"event": "ping"})
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in _connections[job_id]:
            _connections[job_id].remove(websocket)
        logger.debug("WS client disconnected for job %s", job_id)
