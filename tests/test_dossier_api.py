"""
Tests for the dossier API: verdict, pagination, counter-evidence, subroutes.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import src.python.models  # noqa: F401  (registers tables on Base)
from src.python import research_playbook
from src.python.database import get_db, init_db
from src.python.main import app
from src.python.models.evidence import Evidence
from src.python.models.investigation import Investigation
from src.python.routers.dossiers import verdict_for


@pytest.fixture
def client(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'dossier.db'}")
    init_db(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    with Session() as db:
        db.add(
            Investigation(
                target_name="Acme Corp",
                target_id="acme",
                claim_under_investigation="Acme Corp funding",
                status="completed",
                net_confidence_score=0.8,
                playbook_update="lessons_learned_2026-01-01T00:00:00Z",
            )
        )
        db.commit()

    playbook_path = tmp_path / "playbook.mdx"
    playbook_path.write_text(
        "---\nversion: \"1.0.0\"\nlessons_learned:\n"
        "  - label: lessons_learned_2026-01-01T00:00:00Z\n"
        "    claim_type: funding\n"
        "    recorded_at: 2026-01-01T00:00:00Z\n"
        "    gaps: []\n"
        "    successful_tools: [search_username]\n"
        "---\n\n# Playbook\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(research_playbook, "RESEARCH_PLAYBOOK_PATH", playbook_path)

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


def add_evidence(session, claim, confidence=0.8, contradictions=None, corroborating=None,
                 source="SYNINT:WhoisAgent", links=None):
    row = Evidence(
        source=source,
        claim=claim,
        confidence=confidence,
        independence_score=0.7,
        independence_check_details={},
        corroborating_sources=corroborating or [],
        contradictions=contradictions or [],
        links=links or [],
        chain_of_custody=[],
        raw_text="raw",
        investigation_id=1,
        timestamp=datetime(2026, 1, 1),
    )
    session.add(row)
    session.commit()
    return row


class TestVerdict:
    def test_thresholds(self):
        assert verdict_for(0.9) == "supported"
        assert verdict_for(0.5) == "inconclusive"
        assert verdict_for(0.2) == "unsupported"


class TestDossierPayload:
    def test_full_dossier_fields(self, client):
        test_client, Session = client
        with Session() as db:
            add_evidence(db, "Acme funded by Beta", confidence=0.9)
            add_evidence(db, "Acme denies funding", confidence=0.2, contradictions=[1])

        body = test_client.get("/api/dossiers/1").json()

        assert body["verdict"] == "supported"
        assert body["summary"]["evidence_count"] == 2
        assert body["summary"]["high_confidence_count"] == 1
        assert body["summary"]["low_confidence_count"] == 1
        assert body["summary"]["counter_evidence_count"] == 1
        assert body["counter_evidence"][0]["claim"] == "Acme denies funding"
        assert body["investigation"]["playbook_update"].startswith("lessons_learned")

    def test_missing_investigation(self, client):
        test_client, _ = client

        assert test_client.get("/api/dossiers/999").status_code == 404


class TestSubroutes:
    def test_evidence_pagination(self, client):
        test_client, Session = client
        with Session() as db:
            for index in range(12):
                add_evidence(db, f"claim {index}")

        first = test_client.get("/api/dossiers/1/evidence", params={"limit": 5}).json()
        assert first["total"] == 12
        assert len(first["evidence"]) == 5
        assert first["has_more"] is True

        last = test_client.get("/api/dossiers/1/evidence", params={"offset": 10, "limit": 5}).json()
        assert len(last["evidence"]) == 2
        assert last["has_more"] is False

    def test_timeline_subroute(self, client):
        test_client, Session = client
        with Session() as db:
            add_evidence(db, "Acme founded on 1999-04-01")

        body = test_client.get("/api/dossiers/1/timeline").json()

        assert body["events"]
        assert body["events"][0]["timestamp"].startswith("1999-04-01")

    def test_graph_subroute(self, client):
        test_client, Session = client
        with Session() as db:
            add_evidence(db, "Acme Corp acquired Beta Labs")

        body = test_client.get("/api/dossiers/1/graph").json()

        labels = {node["label"] for node in body["nodes"]}
        assert {"Acme Corp", "Beta Labs"} <= labels

    def test_gaps_subroute(self, client):
        test_client, Session = client
        with Session() as db:
            add_evidence(db, "Acme funded by Beta", confidence=0.2)

        body = test_client.get("/api/dossiers/1/gaps").json()

        assert body["claim_type"] == "funding"
        assert body["gaps"]
        assert "weight" in body and "bias" in body

    def test_playbook_update_subroute(self, client):
        test_client, _ = client

        body = test_client.get("/api/dossiers/1/playbook-update").json()

        assert body["reference"] == "lessons_learned_2026-01-01T00:00:00Z"
        assert body["latest_lessons"][0]["label"] == "lessons_learned_2026-01-01T00:00:00Z"

    def test_subroutes_404_for_unknown(self, client):
        test_client, _ = client

        for path in ["evidence", "timeline", "graph", "gaps", "playbook-update"]:
            assert test_client.get(f"/api/dossiers/999/{path}").status_code == 404, path
