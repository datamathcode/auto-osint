"""
In-process event bus for investigation progress.

Runs happen in a worker thread (or a background task); subscribers receive
JSON-serialisable events. Delivery is best-effort: a slow subscriber never
blocks the investigation, and events published when nobody listens are dropped.
"""

import logging
import queue
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

MAX_QUEUE = 500


class EventBus:
    """Fan-out bus keyed by investigation id."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subscribers: Dict[int, List[queue.Queue]] = {}
        self._history: Dict[int, List[Dict[str, Any]]] = {}

    def subscribe(self, investigation_id: int) -> queue.Queue:
        subscriber: queue.Queue = queue.Queue(maxsize=MAX_QUEUE)
        with self._lock:
            self._subscribers.setdefault(investigation_id, []).append(subscriber)
            # Replay recent history so a late subscriber is not blind.
            for event in self._history.get(investigation_id, [])[-50:]:
                subscriber.put(event)
        return subscriber

    def unsubscribe(self, investigation_id: int, subscriber: queue.Queue) -> None:
        with self._lock:
            subscribers = self._subscribers.get(investigation_id, [])
            if subscriber in subscribers:
                subscribers.remove(subscriber)
            if not subscribers:
                self._subscribers.pop(investigation_id, None)

    def publish(self, investigation_id: int, event: Dict[str, Any]) -> None:
        event = {
            "type": event.get("type", "progress"),
            "step": event.get("step"),
            "message": event.get("message", ""),
            "data": event.get("data") or {},
            "progress": event.get("progress"),
            "timestamp": event.get("timestamp")
            or datetime.now(timezone.utc).isoformat(),
        }

        with self._lock:
            self._history.setdefault(investigation_id, []).append(event)
            self._history[investigation_id] = self._history[investigation_id][-200:]
            subscribers = list(self._subscribers.get(investigation_id, []))

        for subscriber in subscribers:
            try:
                subscriber.put_nowait(event)
            except queue.Full:  # pragma: no cover - slow consumer
                logger.warning(
                    f"event queue full for investigation {investigation_id}; dropping event"
                )

    def history(self, investigation_id: int) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._history.get(investigation_id, []))

    def clear(self, investigation_id: int) -> None:
        with self._lock:
            self._history.pop(investigation_id, None)


bus = EventBus()


def sink_for(investigation_id: int):
    """Return a callable suitable for Orchestrator(event_sink=...)."""

    def publish(event: Dict[str, Any]) -> None:
        bus.publish(investigation_id, event)

    return publish
