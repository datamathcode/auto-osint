"""
Ticket 17 end-to-end: submit a synthetic claim, run it asynchronously, watch
progress stream, and read every dossier section back.

Everything is exercised through the real HTTP surface with only the external
tools stubbed (sherlock/holehe/HIBP are not installed in this environment).
"""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import src.python.models  # noqa: F401  (registers tables on Base)
import src.python.research_playbook as research_playbook
from src.python.database import get_db, init_db
from src.python.events import bus
from src.python.main import app
from src.python.models.evidence import Evidence
from src.python.models.investigation import Investigation
from src.python.models.openosint_result import OpenOSINTResult
from src.python.tools.base import ToolBase

CLAIM = "Find all social media accounts and data breaches for target@example.com"


class StubTool(ToolBase):
    def __init__(self, name, payload, fail=False):
        super().__init__(name=name, rate_limit={"requests_per_minute": 0})
        self.tool_name = name
        self.payload = payload
        self.fail = fail

    def execute(self, target, params=None):
        if self.fail:
            return {"status": "failed", "tool": self.tool_name, "target": target,
                    "source": "stub", "data": {}, "error": "upstream unavailable"}
        return {"status": "success", "tool": self.tool_name, "target": target,
                "source": "stub", "data": self.payload, "error": None}


def make_tools(fail_breach=False):
    return {
        "search_email": StubTool("search_email", {
            "email": "target@example.com",
            "count": 2,
            "platforms_found": [
                {"platform": "github", "url": "https://github.com/target"},
                {"platform": "gitlab", "url": "https://gitlab.com/target"},
            ],
        }),
        "search_breach": StubTool("search_breach", {
            "email": "target@example.com",
            "count": 1,
            "breaches": [{"name": "ExampleBreach", "domain": "example.com",
                          "breach_date": "2021-03-04", "data_classes": ["Emails"]}],
        }, fail=fail_breach),
    }


@pytest.fixture
def env(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'e2e.db'}")
    init_db(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    from src.python.routers import orchestration as orchestration_router

    monkeypatch.setattr(orchestration_router, "SessionLocal", Session)
    monkeypatch.setattr(orchestration_router, "build_tools", lambda: make_tools())

    playbook_path = tmp_path / "playbook.mdx"
    playbook_path.write_text("---\nversion: \"1.0.0\"\n---\n\n# Playbook\n\nGuidance.\n",
                             encoding="utf-8")
    monkeypatch.setattr(research_playbook, "RESEARCH_PLAYBOOK_PATH", playbook_path)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app), Session, playbook_path
    finally:
        app.dependency_overrides.clear()
        bus.clear(1)


def start_investigation(client):
    response = client.post(
        "/api/investigations",
        json={
            "target_name": "target@example.com",
            "claim_under_investigation": CLAIM,
            "scope": {
                "platforms": ["github", "gitlab"],
                "data_types": ["social", "breach"],
                "max_execution_minutes": 15,
            },
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def run_async(client, investigation_id):
    response = client.post(
        "/api/orchestrate/async", json={"investigation_id": investigation_id}
    )
    assert response.status_code == 202, response.text
    return response.json()


def sse_events(client, investigation_id):
    with client.stream("GET", f"/sse/investigation/{investigation_id}") as response:
        assert response.status_code == 200
        payload = "".join(response.iter_text())

    return [
        json.loads(line[len("data: "):])
        for line in payload.splitlines()
        if line.startswith("data: ")
    ]


class TestSyntheticInvestigation:
    def test_full_workflow(self, env):
        client, Session, playbook_path = env

        investigation_id = start_investigation(client)
        run_async(client, investigation_id)
        events = sse_events(client, investigation_id)

        # 1. Progress stream covers the whole lifecycle.
        types = [event["type"] for event in events]
        for expected in ["investigation_started", "plan_generated", "finding",
                         "confidence_updated", "refinement", "investigation_complete"]:
            assert expected in types, f"{expected} missing from {types}"
        assert events[-1]["progress"] == 100

        # 2. Evidence and tool results are stored, investigation finished.
        with Session() as db:
            investigation = db.get(Investigation, investigation_id)
            assert investigation.status == "completed"
            assert investigation.net_confidence_score == pytest.approx(0.6)
            assert investigation.playbook_update.startswith("lessons_learned_")

            evidence = db.query(Evidence).filter(
                Evidence.investigation_id == investigation_id
            ).all()
            results = db.query(OpenOSINTResult).filter(
                OpenOSINTResult.investigation_id == investigation_id
            ).all()
            assert len(evidence) >= 2
            assert {row.tool for row in results} == {"search_email", "search_breach"}

        # 3. Recursive improvement actually wrote a lesson.
        assert "lessons_learned" in playbook_path.read_text(encoding="utf-8")

        # 4. Every dossier section is present and populated.
        dossier = client.get(f"/api/dossiers/{investigation_id}").json()
        assert dossier["verdict"] == "inconclusive"
        assert dossier["summary"]["evidence_count"] >= 2
        assert dossier["evidence"][0]["confidence"] is not None

        timeline = client.get(f"/api/dossiers/{investigation_id}/timeline").json()
        assert timeline["events"]
        assert all(event["source"] for event in timeline["events"] if event["role"] != "collection")

        graph = client.get(f"/api/dossiers/{investigation_id}/graph").json()
        assert graph["nodes"]
        assert "metrics" in graph

        gaps = client.get(f"/api/dossiers/{investigation_id}/gaps").json()
        assert "gaps" in gaps and "weight" in gaps and "bias" in gaps

        playbook = client.get(f"/api/dossiers/{investigation_id}/playbook-update").json()
        assert playbook["latest_lessons"], "improvement log should carry the new lesson"

        page = client.get(f"/api/dossiers/{investigation_id}/evidence", params={"limit": 1})
        assert page.json()["has_more"] in {True, False}

    def test_resume_does_not_repeat_completed_tools(self, env):
        client, Session, _ = env

        investigation_id = start_investigation(client)
        run_async(client, investigation_id)

        with Session() as db:
            before = db.query(Evidence).filter(
                Evidence.investigation_id == investigation_id
            ).count()

        response = client.post(
            "/api/orchestrate/async",
            json={"investigation_id": investigation_id, "resume": True},
        )
        assert response.status_code == 202

        with Session() as db:
            after = db.query(Evidence).filter(
                Evidence.investigation_id == investigation_id
            ).count()

        assert after == before, "resume must not re-run completed tools"

    def test_failure_reports_error_and_keeps_progress(self, env, monkeypatch):
        client, Session, _ = env
        from src.python.routers import orchestration as orchestration_router

        monkeypatch.setattr(
            orchestration_router, "build_tools", lambda: make_tools(fail_breach=True)
        )

        investigation_id = start_investigation(client)
        run_async(client, investigation_id)
        events = sse_events(client, investigation_id)

        failures = [
            event for event in events
            if event["type"] == "step_finished" and event["data"].get("status") == "failed"
        ]
        assert failures

        with Session() as db:
            investigation = db.get(Investigation, investigation_id)
            assert investigation.status != "completed"
            stored = db.query(Evidence).filter(
                Evidence.investigation_id == investigation_id
            ).count()
            assert stored >= 1, "progress must survive a partial failure"

    def test_input_validation_blocks_empty_claim(self, env):
        client, _, _ = env

        response = client.post("/api/investigations", json={"target_name": "x"})

        assert response.status_code == 422
