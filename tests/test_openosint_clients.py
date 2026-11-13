"""
Tests for the OpenOSINT clients: parsing, timeout, rate limiting, errors,
persistence, and the results API.
"""

import json
import stat
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import src.python.models  # noqa: F401  (registers tables on Base)
from src.python.database import get_db, init_db
from src.python.main import app
from src.python.models.investigation import Investigation
from src.python.models.openosint_result import OpenOSINTResult
from src.python.tools.clients import (
    SearchBreachClient,
    SearchEmailClient,
    SearchUsernameClient,
)
from src.python.tools.clients.search_email import parse_holehe_output
from src.python.tools.clients.search_username import parse_sherlock_output


def make_binary(path: Path, body: str) -> Path:
    path.write_text(body)
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


# --------------------------------------------------------------------------
# parsing
# --------------------------------------------------------------------------

class TestParsers:
    def test_sherlock_dict_of_urls(self):
        payload = {"github": "https://github.com/alice", "gitlab": "https://gitlab.com/alice"}

        found = parse_sherlock_output(json.dumps(payload))

        assert {"platform": "github", "url": "https://github.com/alice"} in found
        assert len(found) == 2

    def test_sherlock_dict_of_objects_and_sites_wrapper(self):
        payload = {
            "sites": {
                "github": {"url": "https://github.com/alice", "status": "claimed"},
                "old": {"url_main": "https://example.com/alice"},
            }
        }

        found = parse_sherlock_output(json.dumps(payload))

        assert [item["platform"] for item in found] == ["github", "old"]

    def test_sherlock_list_shape(self):
        payload = [{"site": "github", "url": "https://github.com/alice"}]

        assert parse_sherlock_output(json.dumps(payload)) == [
            {"platform": "github", "url": "https://github.com/alice"}
        ]

    def test_sherlock_non_json_returns_empty(self):
        assert parse_sherlock_output("Sherlock is running...\nerror") == []

    def test_holehe_extracts_hits_and_urls(self):
        stdout = (
            "[+] github.com\n"
            "http://github.com/alice\n"
            "[-] twitter.com\n"
            "[+] spotify.com\n"
        )

        found = parse_holehe_output(stdout)

        assert found == [
            {"platform": "github.com", "url": "http://github.com/alice"},
            {"platform": "spotify.com", "url": ""},
        ]


# --------------------------------------------------------------------------
# username client
# --------------------------------------------------------------------------

class TestSearchUsername:
    def test_success_parses_platforms(self, tmp_path):
        binary = make_binary(
            tmp_path / "sherlock",
            "#!/bin/sh\n"
            "echo '{\"github\": \"https://github.com/alice\"}'\n",
        )
        client = SearchUsernameClient(binary=str(binary), rate_limit={"requests_per_minute": 0})

        result = client.execute("alice")

        assert result["status"] == "success"
        assert result["data"]["count"] == 1
        assert result["data"]["platforms_found"][0]["platform"] == "github"
        assert result["source"] == "sherlock"
        assert result["target"] == "alice"

    def test_missing_target(self):
        result = SearchUsernameClient(rate_limit={"requests_per_minute": 0}).execute("")

        assert result["status"] == "failed"
        assert "username is required" in result["error"]

    def test_missing_binary_reports_failure(self):
        client = SearchUsernameClient(binary="/nonexistent/sherlock", rate_limit={"requests_per_minute": 0})

        result = client.execute("alice")

        assert result["status"] == "failed"
        assert "not installed" in result["error"]

    def test_non_json_output_is_partial(self, tmp_path):
        binary = make_binary(tmp_path / "sherlock", "#!/bin/sh\necho 'scanned 400 sites'\n")
        client = SearchUsernameClient(binary=str(binary), rate_limit={"requests_per_minute": 0})

        result = client.execute("alice")

        assert result["status"] == "partial"
        assert result["data"]["count"] == 0
        assert result["data"]["raw"] == "scanned 400 sites"

    def test_timeout_is_enforced(self, tmp_path):
        binary = make_binary(tmp_path / "sherlock", "#!/bin/sh\nsleep 5\n")
        client = SearchUsernameClient(
            binary=str(binary), timeout_seconds=1, rate_limit={"requests_per_minute": 0}
        )

        result = client.execute("alice")

        assert result["status"] == "failed"
        assert "timed out" in result["error"]

    def test_rate_limit_blocks_second_call(self, tmp_path):
        binary = make_binary(tmp_path / "sherlock", "#!/bin/sh\necho '{}'\n")
        client = SearchUsernameClient(binary=str(binary), rate_limit={"requests_per_minute": 1})

        first = client.execute("alice")
        second = client.execute("bob")

        assert first["status"] in {"partial", "success"}
        assert second["status"] == "failed"
        assert "Rate limit exceeded" in second["error"]


# --------------------------------------------------------------------------
# email client
# --------------------------------------------------------------------------

class TestSearchEmail:
    def test_success_parses_platforms(self, tmp_path):
        binary = make_binary(
            tmp_path / "holehe",
            "#!/bin/sh\nprintf '[+] github.com\\nhttp://github.com/alice\\n'\n",
        )
        client = SearchEmailClient(binary=str(binary), rate_limit={"requests_per_minute": 0})

        result = client.execute("alice@example.com")

        assert result["status"] == "success"
        assert result["data"]["email"] == "alice@example.com"
        assert result["data"]["platforms_found"] == [
            {"platform": "github.com", "url": "http://github.com/alice"}
        ]

    def test_invalid_email_rejected(self):
        result = SearchEmailClient(rate_limit={"requests_per_minute": 0}).execute("not-an-email")

        assert result["status"] == "failed"
        assert "invalid email" in result["error"]


# --------------------------------------------------------------------------
# breach client
# --------------------------------------------------------------------------

class FakeResponse:
    def __init__(self, status_code, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


class TestSearchBreach:
    def test_breaches_returned(self, monkeypatch):
        captured = {}

        def fake_get(url, headers=None, timeout=None):
            captured.update({"url": url, "headers": headers, "timeout": timeout})
            return FakeResponse(
                200,
                [
                    {"Name": "Adobe", "Domain": "adobe.com", "BreachDate": "2013-10-04",
                     "DataClasses": ["Email addresses"]},
                ],
            )

        monkeypatch.setattr("src.python.tools.clients.search_breach.requests.get", fake_get)
        client = SearchBreachClient(api_key="test-key", rate_limit={"requests_per_minute": 0})

        result = client.execute("alice@example.com")

        assert result["status"] == "success"
        assert result["data"]["count"] == 1
        assert result["data"]["breaches"][0]["name"] == "Adobe"
        assert captured["headers"]["hibp-api-key"] == "test-key"
        assert captured["timeout"] == 60
        assert "alice%40example.com" in captured["url"]

    def test_no_breaches_404_is_success(self, monkeypatch):
        monkeypatch.setattr(
            "src.python.tools.clients.search_breach.requests.get",
            lambda *a, **k: FakeResponse(404),
        )
        client = SearchBreachClient(api_key="k", rate_limit={"requests_per_minute": 0})

        result = client.execute("alice@example.com")

        assert result["status"] == "success"
        assert result["data"]["count"] == 0

    def test_missing_api_key_fails(self, monkeypatch):
        monkeypatch.delenv("HIBP_API_KEY", raising=False)
        client = SearchBreachClient(rate_limit={"requests_per_minute": 0})

        result = client.execute("alice@example.com")

        assert result["status"] == "failed"
        assert "HIBP_API_KEY" in result["error"]

    def test_bad_key_401(self, monkeypatch):
        monkeypatch.setattr(
            "src.python.tools.clients.search_breach.requests.get",
            lambda *a, **k: FakeResponse(401),
        )
        client = SearchBreachClient(api_key="bad", rate_limit={"requests_per_minute": 0})

        assert "401" in client.execute("alice@example.com")["error"]

    def test_timeout_reported(self, monkeypatch):
        import requests

        def fake_get(*args, **kwargs):
            raise requests.Timeout()

        monkeypatch.setattr("src.python.tools.clients.search_breach.requests.get", fake_get)
        client = SearchBreachClient(api_key="k", rate_limit={"requests_per_minute": 0})

        result = client.execute("alice@example.com")

        assert result["status"] == "failed"
        assert "timed out" in result["error"]


# --------------------------------------------------------------------------
# persistence + API
# --------------------------------------------------------------------------

@pytest.fixture
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'openosint.db'}")
    init_db(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as session:
        session.add(
            Investigation(
                target_name="alice",
                target_id="alice",
                claim_under_investigation="Alice is active on GitHub",
                status="in_progress",
            )
        )
        session.commit()
    return engine


class TestPersistenceAndAPI:
    def test_username_search_end_to_end(self, tmp_path, db):
        binary = make_binary(
            tmp_path / "sherlock",
            "#!/bin/sh\n"
            "echo '{\"github\": \"https://github.com/alice\"}'\n",
        )
        Session = sessionmaker(bind=db)
        with Session() as session:
            client = SearchUsernameClient(
                binary=str(binary), rate_limit={"requests_per_minute": 0}
            )
            client.set_db_session(session)
            result = client.execute("alice")
            result_id = client.persist(result, investigation_id=1)
            session.commit()

            stored = session.get(OpenOSINTResult, result_id)
            assert stored.tool == "search_username"
            assert stored.target == "alice"
            # The result column stores the structured payload (data), while
            # source and error keep their own columns.
            assert stored.result["count"] == 1
            assert stored.result["platforms_found"][0]["platform"] == "github"

        def override_get_db():
            s = Session()
            try:
                yield s
            finally:
                s.close()

        app.dependency_overrides[get_db] = override_get_db
        try:
            client_api = TestClient(app)

            listing = client_api.get("/api/results", params={"target_id": "alice"})
            assert listing.status_code == 200
            rows = listing.json()
            assert len(rows) == 1
            assert rows[0]["tool"] == "search_username"
            assert rows[0]["result"]["platforms_found"][0]["platform"] == "github"

            by_tool = client_api.get("/api/results", params={"tool": "search_username"})
            assert len(by_tool.json()) == 1

            detail = client_api.get(f"/api/results/{rows[0]['id']}")
            assert detail.status_code == 200
            assert detail.json()["target"] == "alice"

            assert client_api.get("/api/results/4242").status_code == 404
            assert client_api.get("/api/results", params={"target_id": "nobody"}).json() == []
        finally:
            app.dependency_overrides.clear()

    def test_persist_without_session_returns_none(self):
        client = SearchUsernameClient(rate_limit={"requests_per_minute": 0})
        result = client.result("success", "alice", data={"count": 0})

        assert client.persist(result, investigation_id=1) is None
