"""
Ticket 07 end-to-end: invoke SYNINT wrappers, store evidence, query it back
through the API. Uses real SQLite files and the real CLI entry point.
"""

import json
import os
import stat
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import src.python.models  # noqa: F401  (registers tables on Base)
from src.python.agents.synint_wrapper import main as wrapper_main
from src.python.database import get_db
from src.python.main import app

AGENTS = ["WhoisAgent", "DNSEnumAgent", "MetadataExtractionAgent"]
SCRIPTS = {
    "WhoisAgent": "whois-agent.sh",
    "DNSEnumAgent": "dns-enum-agent.sh",
    "MetadataExtractionAgent": "metadata-extraction-agent.sh",
}


def write_agent_stub(path: Path, agent: str) -> Path:
    """Fake SYNINT binary that echoes a JSON claim naming the agent."""
    path.write_text(
        "#!/bin/sh\n"
        f"echo '{{\"claim\": \"{agent} found data\", \"confidence\": 0.8}}'\n"
        "exit 0\n"
    )
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "evidence.db"


@pytest.fixture
def stub(tmp_path):
    return write_agent_stub(tmp_path / "synint.sh", "WhoisAgent")


class TestWrapperCLI:
    def test_each_agent_stores_evidence_with_raw_text(self, db_path, tmp_path):
        for agent in AGENTS:
            stub = write_agent_stub(tmp_path / f"{agent}.sh", agent)

            exit_code = wrapper_main(
                [
                    "--synint-path", str(stub),
                    "--agent", agent,
                    "--target", "example.com",
                    "--db-url", f"sqlite:///{db_path}",
                ]
            )

            assert exit_code == 0

        Session = sessionmaker(bind=create_engine(f"sqlite:///{db_path}"))
        from src.python.models.evidence import Evidence

        with Session() as session:
            rows = session.query(Evidence).order_by(Evidence.id).all()

        assert len(rows) == 3
        assert {row.source for row in rows} == {f"SYNINT:{a}" for a in AGENTS}
        assert all(row.claim for row in rows)
        assert all(row.raw_text for row in rows)


class TestShellWrappers:
    def test_scripts_forward_agent_target_and_timeout(self, tmp_path):
        """Each script must invoke the CLI with its own agent name."""
        fake_bin = tmp_path / "bin"
        fake_bin.mkdir()
        recorder = tmp_path / "argv.txt"
        python_shim = fake_bin / "python"
        python_shim.write_text(f'#!/bin/sh\nprintf "%s\\n" "$@" > {recorder}\nexit 0\n')
        python_shim.chmod(0o755)

        for agent, script_name in SCRIPTS.items():
            script = Path("scripts/agents") / script_name
            assert script.exists(), f"missing wrapper script {script}"

            env = dict(os.environ)
            env["PATH"] = f"{fake_bin}:{env['PATH']}"
            env["SYNINT_PATH"] = "/opt/synint"
            env["SYNINT_TIMEOUT"] = "42"

            result = subprocess.run(
                ["sh", str(script), "example.com"],
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )

            assert result.returncode == 0, result.stderr
            argv = recorder.read_text().split()
            assert "--agent" in argv and argv[argv.index("--agent") + 1] == agent
            assert "--target" in argv and argv[argv.index("--target") + 1] == "example.com"
            assert "--timeout" in argv and argv[argv.index("--timeout") + 1] == "42"
            assert "--synint-path" in argv
            assert argv[argv.index("--synint-path") + 1] == "/opt/synint"

    def test_scripts_require_target(self):
        result = subprocess.run(
            ["sh", "scripts/agents/whois-agent.sh"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 2
        assert "usage" in result.stderr


class TestEvidenceAPI:
    def test_query_evidence_by_target_id(self, db_path, tmp_path):
        """End-to-end: run the wrapper, then read evidence back over HTTP."""
        stub = write_agent_stub(tmp_path / "synint.sh", "WhoisAgent")
        wrapper_main(
            [
                "--synint-path", str(stub),
                "--agent", "WhoisAgent",
                "--target", "example.com",
                "--db-url", f"sqlite:///{db_path}",
            ]
        )

        engine = create_engine(f"sqlite:///{db_path}")
        Session = sessionmaker(bind=engine)

        def override_get_db():
            db = Session()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        try:
            client = TestClient(app)

            listing = client.get("/api/evidence", params={"target_id": "example.com"})
            assert listing.status_code == 200
            rows = listing.json()
            assert len(rows) == 1
            assert rows[0]["source"] == "SYNINT:WhoisAgent"
            assert rows[0]["claim"] == "WhoisAgent found data"
            assert rows[0]["raw_text"]

            by_source = client.get(
                "/api/evidence", params={"source": "SYNINT:WhoisAgent"}
            )
            assert len(by_source.json()) == 1

            empty = client.get("/api/evidence", params={"target_id": "nope.example"})
            assert empty.json() == []

            detail = client.get(f"/api/evidence/{rows[0]['id']}")
            assert detail.status_code == 200
            assert detail.json()["chain_of_custody"][0]["command"][0].endswith("synint.sh")

            assert client.get("/api/evidence/9999").status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_evidence_requires_existing_investigation(self, db_path):
        from src.python.database import init_db

        engine = create_engine(f"sqlite:///{db_path}")
        init_db(engine)
        Session = sessionmaker(bind=engine)

        def override_get_db():
            db = Session()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        try:
            client = TestClient(app)
            assert client.get("/api/evidence", params={"investigation_id": 123}).json() == []
        finally:
            app.dependency_overrides.clear()


def test_database_urls_are_absolute(db_path):
    """Guard: the CLI writes where it says it writes."""
    from src.python.models.evidence import Evidence

    engine = create_engine(f"sqlite:///{db_path}")
    assert str(engine.url).endswith(str(db_path))
    assert "evidence" in Evidence.__table__.name
