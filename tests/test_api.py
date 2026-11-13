"""
End-to-end API tests: FastAPI app, routers, ORM models, real SQLite schema.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import src.python.models  # noqa: F401  (registers tables on Base)
from src.python.database import get_db
from src.python.main import app
from src.python.models.base import Base
from src.python.models.evidence import Evidence


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def session(client):
    """Session on the same database the client uses."""
    override = app.dependency_overrides[get_db]
    db = next(override())
    try:
        yield db
    finally:
        db.close()


class TestHealth:
    def test_health_endpoint(self, client):
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestInvestigationsAPI:
    def test_create_investigation(self, client):
        response = client.post(
            "/api/investigations",
            json={
                "target_name": "Example Corp",
                "claim_under_investigation": "Example Corp funded by Acme",
            },
        )

        assert response.status_code == 201
        body = response.json()
        assert body["id"] == 1
        assert body["status"] == "in_progress"

    def test_create_requires_claim(self, client):
        response = client.post("/api/investigations", json={"target_name": "X"})

        assert response.status_code == 422

    def test_list_and_get(self, client):
        client.post(
            "/api/investigations",
            json={"target_name": "A", "claim_under_investigation": "claim A"},
        )
        client.post(
            "/api/investigations",
            json={"target_name": "B", "claim_under_investigation": "claim B"},
        )

        listed = client.get("/api/investigations").json()
        assert [row["target_name"] for row in listed] == ["B", "A"]

        one = client.get("/api/investigations/1")
        assert one.status_code == 200
        assert one.json()["target_name"] == "A"

        missing = client.get("/api/investigations/999")
        assert missing.status_code == 404

    def test_patch_status_and_confidence(self, client):
        client.post(
            "/api/investigations",
            json={"target_name": "A", "claim_under_investigation": "claim A"},
        )

        response = client.patch(
            "/api/investigations/1",
            json={"status": "completed", "net_confidence_score": 0.82},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "completed"
        assert response.json()["net_confidence_score"] == 0.82

    def test_invalid_confidence_rejected(self, client):
        client.post(
            "/api/investigations",
            json={"target_name": "A", "claim_under_investigation": "claim A"},
        )

        response = client.patch(
            "/api/investigations/1", json={"net_confidence_score": 5}
        )

        assert response.status_code == 422


class TestDossiersAPI:
    def test_dossier_compiles_evidence_and_results(self, client, session):
        client.post(
            "/api/investigations",
            json={"target_name": "A", "claim_under_investigation": "claim A"},
        )

        session.add_all(
            [
                Evidence(
                    source="SYNINT:WhoisAgent",
                    claim="Registered to Acme in 2020",
                    confidence=0.8,
                    independence_score=0.9,
                    independence_check_details={"financial_interest": False},
                    corroborating_sources=[],
                    contradictions=[],
                    links=["https://example.com/whois"],
                    chain_of_custody=[{"action": "collected"}],
                    investigation_id=1,
                ),
                Evidence(
                    source="SYNINT:WhoisAgent",
                    claim="Weakly supported claim",
                    confidence=0.2,
                    independence_score=0.5,
                    independence_check_details={},
                    corroborating_sources=[],
                    contradictions=[],
                    links=[],
                    chain_of_custody=[],
                    investigation_id=1,
                ),
            ]
        )
        session.commit()

        dossier = client.get("/api/dossiers/1")

        assert dossier.status_code == 200
        body = dossier.json()
        assert body["summary"]["evidence_count"] == 2
        assert body["summary"]["high_confidence_count"] == 1
        assert body["summary"]["low_confidence_count"] == 1
        assert body["summary"]["mean_confidence"] == 0.5
        assert body["evidence"][0]["claim"] == "Registered to Acme in 2020"

    def test_dossier_missing_investigation(self, client):
        assert client.get("/api/dossiers/42").status_code == 404

    def test_evidence_listing(self, client, session):
        client.post(
            "/api/investigations",
            json={"target_name": "A", "claim_under_investigation": "claim A"},
        )
        session.add(
            Evidence(
                source="SYNINT:WhoisAgent",
                claim="Evidence row",
                confidence=0.6,
                independence_score=0.7,
                independence_check_details={},
                corroborating_sources=[],
                contradictions=[],
                links=["https://example.com"],
                chain_of_custody=[],
                investigation_id=1,
            )
        )
        session.commit()

        response = client.get("/api/investigations/1/evidence")

        assert response.status_code == 200
        assert response.json()[0]["claim"] == "Evidence row"
