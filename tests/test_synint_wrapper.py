"""
Integration tests for the SYNINT agent wrapper.
"""

import json
import subprocess
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.python.agents.synint_wrapper import SYNINTAgentWrapper


def make_wrapper(**kwargs):
    defaults: dict = dict(
        synint_path="/usr/bin/synint",
        name="WhoisAgent",
        investigation_id=1,
        timeout_seconds=5,
        max_retries=0,
    )
    defaults.update(kwargs)
    return SYNINTAgentWrapper(**defaults)


def popen_returning(stdout="", stderr="", returncode=0):
    process = MagicMock()
    process.communicate.return_value = (stdout, stderr)
    process.returncode = returncode
    return process


class TestSYNINTAgentWrapper:
    """Test suite for SYNINTAgentWrapper class."""

    def test_synint_wrapper_initialization(self):
        """Test SYNINT agent wrapper initialization."""
        wrapper = make_wrapper()

        assert wrapper.synint_path == "/usr/bin/synint"
        assert wrapper.name == "WhoisAgent"
        assert wrapper.investigation_id == 1
        assert wrapper.timeout_seconds == 5

    def test_execute_requires_target(self):
        """Test execute fails when target is missing."""
        wrapper = make_wrapper()

        result = wrapper.execute({})

        assert result["status"] == "failed"
        assert "Target must be provided" in result["error"]

    def test_execute_stores_evidence(self):
        """Test that a successful run stores evidence."""
        wrapper = make_wrapper()
        wrapper.set_evidence_storage(Mock())

        stdout = json.dumps({"claim": "Domain example.com registered to Jane"})
        with patch("subprocess.Popen", return_value=popen_returning(stdout=stdout)):
            with patch.object(
                SYNINTAgentWrapper, "store_evidence", return_value=123
            ) as mock_store:
                result = wrapper.execute({
                    "target": "example.com",
                    "agent_name": "WhoisAgent",
                    "stage": "standard",
                })

        assert result["status"] == "success"
        assert result["evidence_id"] == 123
        kwargs = mock_store.call_args.kwargs
        assert kwargs["source"] == "SYNINT:WhoisAgent"
        assert "example.com" in kwargs["claim"]

    def test_execute_fails_on_non_zero_exit(self):
        """Test a non-zero subprocess exit fails the run and stores no evidence."""
        wrapper = make_wrapper()

        with patch("subprocess.Popen", return_value=popen_returning(
            stdout="partial output", returncode=3
        )):
            with patch.object(SYNINTAgentWrapper, "store_evidence") as mock_store:
                result = wrapper.execute({"target": "example.com"})

        assert result["status"] == "failed"
        assert "non-zero exit status 3" in result["error"]
        mock_store.assert_not_called()

    def test_execute_with_timeout(self):
        """Test that a subprocess timeout fails the run and kills the process."""
        wrapper = make_wrapper()

        process = MagicMock()
        # First communicate() times out; the cleanup call after kill() returns.
        process.communicate.side_effect = [
            subprocess.TimeoutExpired("synint", 5),
            ("", ""),
        ]
        process.returncode = None

        with patch("subprocess.Popen", return_value=process):
            with patch.object(SYNINTAgentWrapper, "store_evidence") as mock_store:
                result = wrapper.execute({"target": "example.com"})

        assert result["status"] == "failed"
        assert "timed out" in result["error"].lower()
        process.kill.assert_called_once()
        assert process.communicate.call_count == 2
        mock_store.assert_not_called()

    def test_parse_synint_result_json(self):
        """Test parsing JSON output from SYNINT."""
        result = {
            "stdout": json.dumps({
                "claim": "Domain example.com registered to John Doe",
                "confidence": 0.85,
                "sources": ["whois.com"],
            }),
            "stderr": "",
        }

        parsed = make_wrapper()._parse_synint_result(result)

        assert parsed["claim"] == "Domain example.com registered to John Doe"
        assert parsed["confidence"] == 0.85
        assert parsed["sources"] == ["whois.com"]

    def test_parse_synint_result_fallback(self):
        """Test fallback parsing when output is not JSON."""
        result = {
            "stdout": "Some raw output from SYNINT\nMore lines here",
            "stderr": "",
        }

        parsed = make_wrapper()._parse_synint_result(result)

        assert parsed["claim"].startswith("Some raw output from SYNINT")
        assert parsed["confidence"] == 0.7  # Default confidence


class TestSynintCLI:
    """The wrapper must be runnable as a command, not only as a class."""

    def test_cli_stores_evidence_and_reports_success(self, tmp_path):
        script = tmp_path / "synint.sh"
        script.write_text(
            "#!/bin/sh\n"
            'echo \'{"claim": "Registered to Acme in 2020", "confidence": 0.85}\'\n'
            "exit 0\n"
        )
        script.chmod(0o755)
        db_path = tmp_path / "cli.db"

        from src.python.agents.synint_wrapper import main

        exit_code = main(
            [
                "--synint-path", str(script),
                "--agent", "WhoisAgent",
                "--target", "example.com",
                "--db-url", f"sqlite:///{db_path}",
            ]
        )

        assert exit_code == 0

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from src.python.models.evidence import Evidence
        from src.python.models.investigation import Investigation

        Session = sessionmaker(bind=create_engine(f"sqlite:///{db_path}"))
        with Session() as session:
            investigation = session.query(Investigation).one()
            evidence = session.query(Evidence).one()
            assert investigation.target_name == "example.com"
            assert evidence.confidence == 0.85
            assert evidence.investigation_id == investigation.id

    def test_cli_returns_non_zero_on_failed_agent(self, tmp_path):
        script = tmp_path / "fail.sh"
        script.write_text("#!/bin/sh\nexit 3\n")
        script.chmod(0o755)

        from src.python.agents.synint_wrapper import main

        exit_code = main(
            [
                "--synint-path", str(script),
                "--target", "example.com",
                "--db-url", f"sqlite:///{tmp_path / 'fail.db'}",
                "--max-retries", "0",
            ]
        )

        assert exit_code == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
