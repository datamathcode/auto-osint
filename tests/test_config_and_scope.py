"""
Tests for runtime config defaults and investigation scope input.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import src.python.models  # noqa: F401  (registers tables on Base)
from src.python.database import get_db, init_db
from src.python.main import app
from src.python.models.investigation import Investigation


@pytest.fixture
def client(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'config.db'}")
    init_db(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

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


class TestConfigDefaults:
    def test_defaults_shape(self, client):
        test_client, _ = client

        response = test_client.get("/api/config/defaults")

        assert response.status_code == 200
        body = response.json()
        assert body["llm"]["providers"] == ["anthropic", "openai", "ollama"]
        assert body["database"]["server_side"] is True
        assert body["limits"]["timeout_per_tool_seconds"] >= 1

    def test_secrets_are_never_returned(self, client, monkeypatch):
        test_client, _ = client
        monkeypatch.setenv("HIBP_API_KEY", "super-secret-value")

        response = test_client.get("/api/config/defaults")

        assert response.json()["openosint"]["has_breach_key"] is True
        assert "super-secret-value" not in response.text

    def test_missing_key_reported_as_false(self, client, monkeypatch):
        test_client, _ = client
        monkeypatch.delenv("HIBP_API_KEY", raising=False)

        assert test_client.get("/api/config/defaults").json()["openosint"]["has_breach_key"] is False

    def test_provider_follows_environment(self, client, monkeypatch):
        test_client, _ = client
        monkeypatch.setenv("LLM_PROVIDER", "ollama")

        assert test_client.get("/api/config/defaults").json()["llm"]["provider"] == "ollama"


class TestInvestigationScope:
    def _payload(self, **scope):
        return {
            "target_name": "johndoe",
            "claim_under_investigation": "Find all social accounts for johndoe",
            "scope": {
                "start_date": "2020-01-01",
                "end_date": "2025-12-31",
                "platforms": ["github", "linkedin"],
                "data_types": ["social", "news"],
                "max_execution_minutes": 30,
                **scope,
            },
        }

    def test_scope_persisted_and_returned(self, client):
        test_client, Session = client

        response = test_client.post("/api/investigations", json=self._payload())

        assert response.status_code == 201
        body = response.json()
        assert body["scope"]["platforms"] == ["github", "linkedin"]
        assert body["scope"]["max_execution_minutes"] == 30

        with Session() as db:
            stored = db.get(Investigation, body["id"])
            assert stored.scope["data_types"] == ["social", "news"]

    def test_scope_is_optional(self, client):
        test_client, _ = client

        response = test_client.post(
            "/api/investigations",
            json={"target_name": "a", "claim_under_investigation": "b"},
        )

        assert response.status_code == 201
        assert response.json()["scope"] is None

    def test_reversed_dates_rejected(self, client):
        test_client, _ = client

        response = test_client.post(
            "/api/investigations",
            json=self._payload(start_date="2025-01-01", end_date="2020-01-01"),
        )

        assert response.status_code == 422
        assert "end_date" in response.json()["detail"]

    def test_execution_time_bounds(self, client):
        test_client, _ = client

        too_short = test_client.post(
            "/api/investigations", json=self._payload(max_execution_minutes=1)
        )
        too_long = test_client.post(
            "/api/investigations", json=self._payload(max_execution_minutes=120)
        )

        assert too_short.status_code == 422
        assert too_long.status_code == 422

    def test_required_fields(self, client):
        test_client, _ = client

        assert test_client.post("/api/investigations", json={"target_name": "x"}).status_code == 422
