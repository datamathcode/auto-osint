"""
Tests for progress streaming: event bus, orchestrator events, async run,
SSE and WebSocket endpoints.
"""

import json
import threading
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import src.python.models  # noqa: F401  (registers tables on Base)
from src.python.database import get_db, init_db
from src.python.events import EventBus, bus
from src.python.main import app
from src.python.models.investigation import Investigation
from src.python.orchestrator import Orchestrator
from src.python.tools.base import ToolBase


class StubTool(ToolBase):
    def __init__(self, name="search_username", payload=None):
        super().__init__(name=name, rate_limit={"requests_per_minute": 0})
        self.tool_name = name
        self.payload = payload or {"count": 1, "platforms_found": [
            {"platform": "github", "url": "https://github.com/johndoe"}
        ]}

    def execute(self, target, params=None):
        return {
            "status": "success",
            "tool": self.tool_name,
            "target": target,
            "source": "stub",
            "data": self.payload,
            "error": None,
        }


class TestEventBus:
    def test_publish_delivers_to_subscriber(self):
        local = EventBus()
        subscriber = local.subscribe(1)

        local.publish(1, {"type": "plan_generated", "message": "planned"})

        event = subscriber.get(timeout=1)
        assert event["type"] == "plan_generated"
        assert event["timestamp"]

    def test_history_replayed_to_late_subscriber(self):
        local = EventBus()
        local.publish(1, {"type": "investigation_started"})
        local.publish(1, {"type": "investigation_complete"})

        subscriber = local.subscribe(1)

        assert subscriber.get(timeout=1)["type"] == "investigation_started"
        assert subscriber.get(timeout=1)["type"] == "investigation_complete"

    def test_unsubscribe_stops_delivery(self):
        local = EventBus()
        subscriber = local.subscribe(1)
        local.unsubscribe(1, subscriber)

        local.publish(1, {"type": "finding"})

        assert subscriber.empty()

    def test_slow_subscriber_does_not_block(self):
        local = EventBus()
        subscriber = local.subscribe(1)
        for index in range(600):  # exceeds MAX_QUEUE
            local.publish(1, {"type": "finding", "message": str(index)})

        assert subscriber.qsize() <= 500


class TestOrchestratorEvents:
    def test_emits_full_sequence(self, tmp_path):
        engine = create_engine(f"sqlite:///{tmp_path / 'events.db'}")
        init_db(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        session.add(Investigation(target_name="johndoe", claim_under_investigation="Find accounts",
                                  status="in_progress"))
        session.commit()

        seen = []
        orchestrator = Orchestrator(
            tools={"search_username": StubTool()},
            session=session,
            investigation_id=1,
            event_sink=seen.append,
        )

        orchestrator.run("Find all social accounts for johndoe", "johndoe")

        types = [event["type"] for event in seen]
        for expected in [
            "investigation_started",
            "plan_generated",
            "step_started",
            "finding",
            "step_finished",
            "confidence_updated",
            "refinement",
            "investigation_complete",
        ]:
            assert expected in types, f"missing {expected} in {types}"

        assert seen[0]["progress"] == 5
        assert seen[-1]["progress"] == 100
        session.close()

    def test_no_sink_is_safe(self):
        orchestrator = Orchestrator(tools={"search_username": StubTool()})

        orchestrator.run("Find accounts", "johndoe")  # must not raise

    def test_failing_sink_does_not_break_run(self):
        def boom(event):
            raise RuntimeError("sink down")

        orchestrator = Orchestrator(
            tools={"search_username": StubTool()}, event_sink=boom
        )

        result = orchestrator.run("Find accounts", "johndoe")

        assert result["report"]["summary"]["succeeded"] == 1


@pytest.fixture
def client(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'stream.db'}")
    init_db(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as db:
        db.add(
            Investigation(
                target_name="johndoe",
                target_id="johndoe",
                claim_under_investigation="Find all social accounts for johndoe",
                status="in_progress",
            )
        )
        db.commit()

    from src.python.routers import orchestration as orchestration_router

    monkeypatch.setattr(
        orchestration_router, "build_tools", lambda: {"search_username": StubTool()}
    )
    # The background run opens its own SessionLocal; point it at the test DB.
    monkeypatch.setattr(
        orchestration_router,
        "SessionLocal",
        sessionmaker(bind=engine, expire_on_commit=False),
    )

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app), Session
    finally:
        app.dependency_overrides.clear()
        bus.clear(1)


class TestAsyncAndSSE:
    def test_async_run_returns_202_and_completes(self, client):
        test_client, Session = client

        response = test_client.post("/api/orchestrate/async", json={"investigation_id": 1})

        assert response.status_code == 202
        body = response.json()
        assert body["status"] == "started"
        assert body["sse_url"].endswith("/1")

        with Session() as db:
            investigation = db.get(Investigation, 1)
            assert investigation.status == "completed"
            assert investigation.net_confidence_score == 0.6

    def test_sse_stream_contains_progress_events(self, client):
        test_client, _ = client
        test_client.post("/api/orchestrate/async", json={"investigation_id": 1})

        with test_client.stream("GET", "/sse/investigation/1") as response:
            assert response.status_code == 200
            payload = "".join(response.iter_text())

        events = [
            json.loads(line[len("data: "):])
            for line in payload.splitlines()
            if line.startswith("data: ")
        ]
        types = [event["type"] for event in events]

        assert "investigation_started" in types
        assert "investigation_complete" in types
        assert events[-1]["progress"] == 100

    def test_sse_unknown_investigation_is_404(self, client):
        test_client, _ = client

        response = test_client.get("/sse/investigation/999")

        assert response.status_code == 404

    def test_async_unknown_investigation(self, client):
        test_client, _ = client

        assert test_client.post(
            "/api/orchestrate/async", json={"investigation_id": 999}
        ).status_code == 404


class TestWebSocket:
    def test_websocket_delivers_events(self, client):
        test_client, _ = client
        test_client.post("/api/orchestrate/async", json={"investigation_id": 1})

        received = []
        with test_client.websocket_connect("/ws/investigation/1") as websocket:
            while True:
                event = websocket.receive_json()
                if event["type"] == "heartbeat":
                    continue
                received.append(event)
                if event["type"] == "investigation_complete":
                    break

        assert received[0]["type"] == "investigation_started"
        assert received[-1]["type"] == "investigation_complete"
