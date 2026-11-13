"""
Progress streaming: Server-Sent Events and WebSocket endpoints.

Both read from the in-process EventBus, replay recent history to late
subscribers, and finish when an ``investigation_complete`` event arrives.
"""

import asyncio
import json
import logging
import queue
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from ..database import get_db
from ..events import bus
from ..models.investigation import Investigation

logger = logging.getLogger(__name__)

sse_router = APIRouter()
ws_router = APIRouter()

TERMINAL_EVENTS = {"investigation_complete"}
HEARTBEAT_SECONDS = 15


async def _next_event(subscriber: queue.Queue, timeout: float) -> Dict[str, Any] | None:
    try:
        return await asyncio.to_thread(subscriber.get, True, timeout)
    except queue.Empty:
        return None


@sse_router.get("/investigation/{investigation_id}")
async def stream_investigation(
    investigation_id: int, db: Session = Depends(get_db)
):
    """Server-Sent Events stream of investigation progress."""
    if db.get(Investigation, investigation_id) is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    async def event_stream():
        subscriber = bus.subscribe(investigation_id)
        try:
            while True:
                event = await _next_event(subscriber, HEARTBEAT_SECONDS)
                if event is None:
                    yield ": keep-alive\n\n"
                    continue
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("type") in TERMINAL_EVENTS:
                    break
        finally:
            bus.unsubscribe(investigation_id, subscriber)

    from fastapi.responses import StreamingResponse

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@ws_router.websocket("/investigation/{investigation_id}")
async def websocket_investigation(websocket: WebSocket, investigation_id: int):
    """WebSocket stream of investigation progress."""
    await websocket.accept()
    subscriber = bus.subscribe(investigation_id)

    try:
        while True:
            event = await _next_event(subscriber, HEARTBEAT_SECONDS)
            if event is None:
                await websocket.send_json({"type": "heartbeat"})
                continue
            await websocket.send_json(event)
            if event.get("type") in TERMINAL_EVENTS:
                break
    except WebSocketDisconnect:
        pass
    except Exception as exc:  # pragma: no cover - transport failure
        logger.warning(f"websocket stream failed for {investigation_id}: {exc}")
    finally:
        bus.unsubscribe(investigation_id, subscriber)
        try:
            await websocket.close()
        except RuntimeError:
            pass
