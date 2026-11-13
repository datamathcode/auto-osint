"""
Tests for the post-investigation learning loop.
"""

import pathlib
from typing import Any, Dict, Optional

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import src.python.models  # noqa: F401  (registers tables on Base)
from src.python import learning, research_playbook
from src.python.database import init_db
from src.python.models.evidence import Evidence
from src.python.models.investigation import Investigation
from src.python.models.openosint_result import OpenOSINTResult
from src.python.orchestrator import Orchestrator
from src.python.tools.base import ToolBase


class StubTool(ToolBase):
    def __init__(self, name: str, payload: Dict[str, Any], fail: bool = False):
        super().__init__(name=name, rate_limit={"requests_per_minute": 0})
        self.tool_name = name
        self.payload = payload
        self.fail = fail

    def execute(self, target: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self.fail:
            return {"status": "failed", "tool": self.tool_name, "target": target,
                    "source": "stub", "data": {}, "error": "boom"}
        return {"status": "success", "tool": self.tool_name, "target": target,
                "source": "stub", "data": self.payload, "error": None}


@pytest.fixture
def session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'learning.db'}")
    init_db(engine)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        db.add(
            Investigation(
                target_name="johndoe",
                target_id="johndoe",
                claim_under_investigation="Find all social accounts for johndoe",
                status="completed",
            )
        )
        db.add(
            Investigation(
                target_name="other",
                target_id="other",
                claim_under_investigation="Investigate funding for Other",
                status="completed",
            )
        )
        db.commit()
    return Session


@pytest.fixture
def playbook_path(tmp_path, monkeypatch):
    path = pathlib.Path(tmp_path) / "research_playbook.mdx"
    path.write_text("---\nversion: \"1.0.0\"\n---\n\n# Playbook\n\nGuidance.\n", encoding="utf-8")
    monkeypatch.setattr(research_playbook, "RESEARCH_PLAYBOOK_PATH", path)
    return path


def add_result(session, investigation_id, tool, error=None):
    session.add(
        OpenOSINTResult(
            tool=tool,
            target="johndoe",
            result={"count": 1},
            source=tool,
            error=error,
            investigation_id=investigation_id,
        )
    )


class TestAnalysis:
    def test_gaps_and_patterns_from_results(self, session):
        db = session()
        add_result(db, 1, "search_username")
        add_result(db, 1, "search_breach", error="HIBP key missing")
        db.add(
            Evidence(
                source="search_username",
                claim="found 1 record",
                confidence=0.6,
                independence_score=0.7,
                independence_check_details={},
                corroborating_sources=[],
                contradictions=[],
                links=["https://github.com/johndoe"],
                chain_of_custody=[],
                investigation_id=1,
            )
        )
        db.commit()

        analysis = learning.analyze_investigation(db, 1)

        assert analysis.claim_type == "social_presence"
        assert analysis.evidence_count == 1
        assert "search_username" in analysis.successful_tools
        assert "search_breach" in analysis.failed_tools
        assert any("HIBP key missing" in gap for gap in analysis.gaps)
        assert any("productive sources" in pattern for pattern in analysis.patterns)
        db.close()

    def test_empty_investigation_reports_missing_evidence(self, session):
        db = session()
        analysis = learning.analyze_investigation(db, 1)

        assert any("no evidence" in gap for gap in analysis.gaps)
        assert any("no tool results" in gap for gap in analysis.gaps)
        db.close()

    def test_unknown_investigation_raises(self, session):
        db = session()
        with pytest.raises(ValueError, match="not found"):
            learning.analyze_investigation(db, 999)
        db.close()


class TestPlaybookUpdate:
    def test_update_appends_lesson_and_preserves_body(self, session, playbook_path):
        db = session()
        add_result(db, 1, "search_username")
        db.commit()

        result = learning.run_post_investigation(db, 1, path=playbook_path)

        assert result["playbook_update"].startswith("lessons_learned_")
        text = playbook_path.read_text(encoding="utf-8")
        assert "Guidance." in text, "saving a lesson must not delete the body"
        metadata = research_playbook.load()
        assert len(metadata["lessons_learned"]) == 1
        assert metadata["lessons_learned"][0]["claim_type"] == "social_presence"

        db.refresh(db.get(Investigation, 1))
        assert db.get(Investigation, 1).playbook_update == result["playbook_update"]
        db.close()

    def test_lessons_are_incremental_and_capped(self, session, playbook_path):
        db = session()
        add_result(db, 1, "search_username")
        db.commit()

        for index in range(12):
            analysis = learning.InvestigationAnalysis(
                investigation_id=1,
                claim_type="social_presence",
                successful_tools=["search_username"],
            )
            learning.update_playbook(analysis, path=playbook_path, label=f"2026-01-01T00:00:{index:02d}Z")

        metadata = research_playbook.load()
        assert len(metadata["lessons_learned"]) == learning.MAX_LESSONS_RETAINED
        assert metadata["lessons_learned"][-1]["recorded_at"].endswith(":11Z")
        db.close()

    def test_existing_sections_survive(self, session, playbook_path):
        db = session()
        add_result(db, 1, "search_username")
        db.commit()

        before = research_playbook.load()
        learning.run_post_investigation(db, 1, path=playbook_path)
        after = research_playbook.load()

        assert after["version"] == before["version"]
        assert "funding" not in before  # fixture playbook is minimal
        db.close()


class TestNextInvestigation:
    def test_lessons_reorder_tool_selection(self, session, playbook_path):
        db = session()
        add_result(db, 1, "search_username")
        db.commit()
        learning.run_post_investigation(db, 1, path=playbook_path)
        db.close()

        tools = {
            "search_email": StubTool("search_email", {"count": 1}),
            "search_username": StubTool("search_username", {"count": 1}),
        }
        orchestrator = Orchestrator(tools=tools, playbook_loader=research_playbook.load)

        plan = orchestrator.plan_investigation("Find all social accounts", "johndoe")

        assert plan.steps[0].tool == "search_username"


class TestIntegration:
    def test_run_analyze_update_run_again(self, tmp_path, session, playbook_path):
        """Full loop: investigation -> analysis -> playbook update -> next run uses it."""
        db = session()
        tool = StubTool(
            "search_username",
            {"count": 1, "platforms_found": [{"platform": "github", "url": "https://github.com/johndoe"}]},
        )
        first = Orchestrator(
            tools={"search_username": tool},
            session=db,
            investigation_id=1,
            playbook_loader=research_playbook.load,
        )
        first.run("Find all social accounts for johndoe", "johndoe")

        post = learning.run_post_investigation(db, 1, path=playbook_path)
        assert post["analysis"]["successful_tools"] == ["search_username"]
        assert post["analysis"]["result_count"] == 1
        assert db.query(OpenOSINTResult).count() == 1
        assert db.get(Investigation, 1).playbook_update.startswith("lessons_learned_")

        # Second investigation plans with the learned lesson available.
        second = Orchestrator(
            tools={
                "search_email": StubTool("search_email", {"count": 1}),
                "search_username": StubTool("search_username", {"count": 1}),
            },
            playbook_loader=research_playbook.load,
        )
        plan = second.plan_investigation("Find all social accounts for johndoe", "johndoe")

        assert plan.steps[0].tool == "search_username"
        assert learning.recommended_tools(research_playbook.load(), "social_presence") == [
            "search_username"
        ]
        db.close()
