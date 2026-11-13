"""
Tests for the orchestration layer: planning, parallel execution, observation,
reasoning, refinement, and a full end-to-end investigation.
"""

import time
from typing import Any, Dict, Optional

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import src.python.models  # noqa: F401  (registers tables on Base)
from src.python.database import init_db
from src.python.models.evidence import Evidence
from src.python.models.investigation import Investigation
from src.python.orchestrator import (
    Orchestrator,
    classify_claim,
    classify_target,
)
from src.python.tools.base import ToolBase
from src.python.tools.clients import SearchBreachClient, SearchUsernameClient


class StubTool(ToolBase):
    """Deterministic tool returning a fixed envelope, with optional delay."""

    def __init__(self, name: str, payload: Dict[str, Any], delay: float = 0.0, fail: bool = False):
        super().__init__(name=name, rate_limit={"requests_per_minute": 0})
        self.tool_name = name
        self.payload = payload
        self.delay = delay
        self.fail = fail
        self.calls = 0

    def execute(self, target: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.calls += 1
        if self.delay:
            time.sleep(self.delay)
        if self.fail:
            return {
                "status": "failed",
                "tool": self.tool_name,
                "target": target,
                "source": "stub",
                "data": {},
                "error": "stub failure",
            }
        return {
            "status": "success",
            "tool": self.tool_name,
            "target": target,
            "source": "stub",
            "data": self.payload,
            "error": None,
        }


class TestClassification:
    def test_target_kinds(self):
        assert classify_target("alice@example.com") == "email"
        assert classify_target("example.com") == "domain"
        assert classify_target("johndoe") == "username"

    def test_claim_types(self):
        assert classify_claim("Investigate funding for Acme") == "funding"
        assert classify_claim("Who holds the patent on this widget") == "intellectual_property"
        assert classify_claim("Find all social accounts for johndoe") == "social_presence"
        assert classify_claim("Check this rumour") == "general"


class TestPlanning:
    def test_username_claim_plans_username_tool(self):
        orchestrator = Orchestrator(tools={"search_username": StubTool("search_username", {"count": 1, "platforms_found": []})})

        plan = orchestrator.plan_investigation("Find all social accounts for johndoe", "johndoe")

        assert plan.claim_type == "social_presence"
        assert [step.tool for step in plan.steps] == ["search_username"]

    def test_email_target_plans_email_and_breach(self):
        orchestrator = Orchestrator(
            tools={
                "search_email": StubTool("search_email", {"count": 1, "platforms_found": []}),
                "search_breach": StubTool("search_breach", {"count": 1, "breaches": []}),
            }
        )

        plan = orchestrator.plan_investigation("Check this email", "alice@example.com")

        assert [step.tool for step in plan.steps] == ["search_email", "search_breach"]

    def test_funding_claim_adds_playbook_steps(self):
        orchestrator = Orchestrator(
            tools={"search_username": StubTool("search_username", {})},
            playbook_loader=lambda: {"funding": {"suggested_tools": ["SEC filings"]}},
        )

        plan = orchestrator.plan_investigation("Investigate funding for Acme", "johndoe")

        labels = [step.tool for step in plan.steps]
        assert "SEC filings" in labels
        optional = {step.tool: step.optional for step in plan.steps}
        assert optional["SEC filings"] is True

    def test_playbook_tool_resolves_to_registered_client(self):
        orchestrator = Orchestrator(
            tools={"search_username": StubTool("search_username", {})},
            playbook_loader=lambda: {"general": {"suggested_tools": ["search_username"]}},
        )

        plan = orchestrator.plan_investigation("Check this rumour", "johndoe")

        assert any(step.tool == "search_username" and not step.optional for step in plan.steps)

    def test_broken_playbook_does_not_stop_planning(self):
        def boom():
            raise RuntimeError("playbook unreadable")

        orchestrator = Orchestrator(
            tools={"search_username": StubTool("search_username", {})},
            playbook_loader=boom,
        )

        plan = orchestrator.plan_investigation("Find accounts", "johndoe")

        assert plan.steps[0].tool == "search_username"


class TestExecution:
    def test_parallel_execution_is_concurrent(self):
        slow_a = StubTool("slow_a", {"count": 1}, delay=0.4)
        slow_b = StubTool("slow_b", {"count": 1}, delay=0.4)
        orchestrator = Orchestrator(
            tools={"search_username": slow_a},
            max_concurrent=2,
        )
        plan = orchestrator.plan_investigation("Find accounts", "johndoe")
        plan.steps.append(type(plan.steps[0])(tool="slow_b", target="johndoe", rationale="extra"))
        orchestrator.tools["slow_b"] = slow_b

        started = time.time()
        report = orchestrator.execute_plan(plan)
        elapsed = time.time() - started

        assert report["summary"]["succeeded"] == 2
        assert elapsed < 0.75, f"expected concurrent execution, took {elapsed:.2f}s"

    def test_failed_tool_is_reported_not_raised(self):
        orchestrator = Orchestrator(tools={"search_username": StubTool("search_username", {}, fail=True)})

        report = orchestrator.execute_plan(
            orchestrator.plan_investigation("Find accounts", "johndoe")
        )

        assert report["summary"]["failed"] == 1
        assert "stub failure" in report["results"][0]["error"]

    def test_unregistered_tool_step_is_skipped(self):
        orchestrator = Orchestrator(tools={})
        plan = orchestrator.plan_investigation("Investigate funding", "acme.com")

        report = orchestrator.execute_plan(plan)

        statuses = [result["status"] for result in report["results"]]
        assert "skipped" in statuses


class TestObservationAndReasoning:
    def test_observation_records_finding_and_confidence(self):
        sessions = []

        orchestrator = Orchestrator(
            tools={"search_username": StubTool("search_username", {"count": 2, "platforms_found": [{"platform": "github", "url": "https://github.com/johndoe"}]})}
        )
        report = orchestrator.execute_plan(
            orchestrator.plan_investigation("Find accounts", "johndoe")
        )

        observation = orchestrator.observe_tool_output(report["results"][0])
        orchestrator.update_reasoning()

        assert observation["claim"].startswith("search_username found 2")
        assert observation["tool"] == "search_username"
        assert orchestrator.state.as_dict()["confidence"] == 0.6
        assert not sessions

    def test_failure_becomes_a_gap(self):
        orchestrator = Orchestrator(tools={"search_username": StubTool("search_username", {}, fail=True)})
        report = orchestrator.execute_plan(
            orchestrator.plan_investigation("Find accounts", "johndoe")
        )

        orchestrator.observe_tool_output(report["results"][0])

        assert orchestrator.state.gaps
        assert "search_username" in orchestrator.state.gaps[0]

    def test_identify_gaps_lists_skipped_and_partial(self):
        orchestrator = Orchestrator(tools={})
        plan = orchestrator.plan_investigation("Investigate funding", "acme.com")
        report = orchestrator.execute_plan(plan)

        gaps = orchestrator.identify_gaps(report)

        assert gaps


class TestEndToEnd:
    def test_synthetic_claim_runs_full_pipeline(self, tmp_path):
        """Plan -> parallel execute -> observe -> store evidence -> refine."""
        engine = create_engine(f"sqlite:///{tmp_path / 'orchestrator.db'}")
        init_db(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        session.add(
            Investigation(
                target_name="johndoe",
                target_id="johndoe",
                claim_under_investigation="Find all social accounts for johndoe",
                status="in_progress",
            )
        )
        session.commit()

        username_tool = StubTool(
            "search_username",
            {
                "username": "johndoe",
                "count": 2,
                "platforms_found": [
                    {"platform": "github", "url": "https://github.com/johndoe"},
                    {"platform": "gitlab", "url": "https://gitlab.com/johndoe"},
                ],
            },
        )
        orchestrator = Orchestrator(
            tools={"search_username": username_tool},
            session=session,
            investigation_id=1,
        )

        result = orchestrator.run("Find all social accounts for johndoe", "johndoe")

        assert result["plan"]["claim_type"] == "social_presence"
        assert result["report"]["summary"]["succeeded"] == 1
        assert result["reasoning"]["finding_count"] == 1
        assert result["reasoning"]["confidence"] == 0.6

        rows = session.query(Evidence).all()
        assert len(rows) == 1
        assert rows[0].source == "stub"
        assert "found 2 records" in rows[0].claim
        assert "https://github.com/johndoe" in rows[0].links

        session.close()

    def test_run_stops_after_iterations_without_duplicate_work(self, tmp_path):
        tool = StubTool("search_username", {"count": 1, "platforms_found": []})
        orchestrator = Orchestrator(
            tools={"search_username": tool}, max_iterations=3
        )

        orchestrator.run("Find accounts for johndoe", "johndoe")

        # One pass only: the refinement finds no new steps to run.
        assert tool.calls == 1

    def test_reasoning_hook_receives_state(self):
        seen = {}

        def hook(plan, report, state):
            seen["claim"] = plan.claim
            seen["steps"] = report["summary"]["steps"]
            seen["confidence"] = state.confidence

        orchestrator = Orchestrator(
            tools={"search_username": StubTool("search_username", {"count": 1})},
            reasoning_hook=hook,
        )

        orchestrator.run("Find accounts for johndoe", "johndoe")

        assert seen["claim"] == "Find accounts for johndoe"
        assert seen["steps"] >= 1
        assert seen["confidence"] == 0.6


class TestWithRealClients:
    def test_real_username_client_through_orchestrator(self, tmp_path):
        binary = tmp_path / "sherlock"
        binary.write_text(
            "#!/bin/sh\n"
            "echo '{\"github\": \"https://github.com/johndoe\"}'\n"
        )
        binary.chmod(0o755)

        client = SearchUsernameClient(
            binary=str(binary), rate_limit={"requests_per_minute": 0}
        )
        orchestrator = Orchestrator(tools={"search_username": client})

        result = orchestrator.run("Find all social accounts for johndoe", "johndoe")

        assert result["report"]["summary"]["succeeded"] == 1
        assert result["reasoning"]["finding_count"] == 1

    def test_breach_client_error_is_a_gap(self, monkeypatch):
        monkeypatch.delenv("HIBP_API_KEY", raising=False)
        client = SearchBreachClient(rate_limit={"requests_per_minute": 0})
        orchestrator = Orchestrator(tools={"search_breach": client})

        result = orchestrator.run("Check this email", "alice@example.com")

        assert result["report"]["summary"]["failed"] >= 1
        assert any("HIBP_API_KEY" in gap for gap in result["reasoning"]["gaps"])


class TestOrchestrationEndpoint:
    @pytest.fixture
    def client(self, tmp_path, monkeypatch):
        from fastapi.testclient import TestClient

        from src.python.database import get_db
        from src.python.main import app
        from src.python.routers import orchestration as orchestration_router

        engine = create_engine(f"sqlite:///{tmp_path / 'api.db'}")
        init_db(engine)
        Session = sessionmaker(bind=engine, expire_on_commit=False)
        with Session() as session:
            session.add(
                Investigation(
                    target_name="johndoe",
                    target_id="johndoe",
                    claim_under_investigation="Find all social accounts for johndoe",
                    status="in_progress",
                )
            )
            session.commit()

        monkeypatch.setattr(
            orchestration_router,
            "build_tools",
            lambda: {
                "search_username": StubTool(
                    "search_username",
                    {
                        "username": "johndoe",
                        "count": 1,
                        "platforms_found": [
                            {"platform": "github", "url": "https://github.com/johndoe"}
                        ],
                    },
                )
            },
        )

        def override_get_db():
            session = Session()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_db] = override_get_db
        try:
            yield TestClient(app), Session
        finally:
            app.dependency_overrides.clear()

    def test_orchestrate_runs_and_updates_investigation(self, client):
        test_client, Session = client

        response = test_client.post("/api/orchestrate", json={"investigation_id": 1})

        assert response.status_code == 200
        body = response.json()
        assert body["plan"]["claim_type"] == "social_presence"
        assert body["report"]["summary"]["succeeded"] == 1
        assert body["reasoning"]["confidence"] == 0.6

        with Session() as session:
            investigation = session.get(Investigation, 1)
            assert investigation.net_confidence_score == 0.6
            assert investigation.status == "completed"
            assert "search_username" in investigation.stages_completed
            assert session.query(Evidence).count() == 1

    def test_orchestrate_missing_investigation(self, client):
        test_client, _ = client

        response = test_client.post("/api/orchestrate", json={"investigation_id": 99})

        assert response.status_code == 404
