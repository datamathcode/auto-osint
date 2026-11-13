"""
SYNINT agent shell wrapper for auto-osint.

This module provides a wrapper that executes SYNINT agents from the command line
and stores results as evidence in the database.
"""

import json
import logging
import subprocess
from typing import Any, Dict, List, Optional

from ..agents.base import AgentBase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SYNINTAgentWrapper(AgentBase):
    """
    Wrapper for executing SYNINT agents from the command line.

    This agent wrapper executes SYNINT agents as subprocesses and stores
    the results as evidence in the database.
    """

    def __init__(
        self,
        synint_path: str,
        name: str,
        investigation_id: int,
        timeout_seconds: int = 300,
        max_retries: int = 2,
    ):
        """
        Initialize the SYNINT agent wrapper.

        Args:
            synint_path: Path to SYNINT binary
            name: Agent name to pass to SYNINT (e.g., "WhoisAgent")
            investigation_id: Associated investigation ID
            timeout_seconds: Maximum execution time
            max_retries: Maximum number of retry attempts
        """
        super().__init__(
            name=name,
            investigation_id=investigation_id,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )
        self.synint_path = synint_path

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the SYNINT agent.

        Args:
            context: Investigation context with target info and parameters

        Returns:
            Dict with execution results, status, and observations
        """
        self.reset_observation_buffer()
        self.observe({"type": "execution_started", "context": context})

        try:
            # Build SYNINT command
            agent_name = context.get("agent_name", self.name)
            target = context.get("target")
            stage = context.get("stage", "standard")

            if not target:
                raise ValueError("Target must be provided in context")

            # Construct SYNINT command
            cmd = [
                self.synint_path,
                "run",
                "--agent", agent_name,
                "--target", target,
                "--stage", stage,
            ]

            logger.info(f"Executing SYNINT agent: {' '.join(cmd)}")

            # Execute SYNINT
            result = self._execute_with_retry(
                lambda: self._run_synint_agent(cmd)
            )

            # Parse results
            parsed_result = self._parse_synint_result(result)

            # Store evidence
            evidence_id = self.store_evidence(
                source=f"SYNINT:{agent_name}",
                claim=parsed_result.get("claim", "No claim extracted"),
                confidence=parsed_result.get("confidence", 0.5),
                independence_score=parsed_result.get("independence_score", 0.5),
                independence_check_details=parsed_result.get("independence_check_details"),
                links=parsed_result.get("links"),
                raw_text=result.get("stdout", ""),
                chain_of_custody=[{
                    "timestamp": self.observation_buffer[-1].get("timestamp"),
                    "command": cmd,
                    "stdout": result.get("stdout", ""),
                    "stderr": result.get("stderr", ""),
                }],
            )

            # Update observation buffer
            self.observe({
                "type": "evidence_stored",
                "evidence_id": evidence_id,
                "claim": parsed_result.get("claim"),
            })

            # Return result
            return {
                "status": "success",
                "agent": agent_name,
                "target": target,
                "result": parsed_result,
                "evidence_id": evidence_id,
                "summary": {
                    "claim": parsed_result.get("claim"),
                    "confidence": parsed_result.get("confidence"),
                    "evidence_id": evidence_id,
                    "exit_code": result.get("returncode", 0),
                },
                "observations": self.get_observation_buffer(),
            }

        except Exception as e:
            logger.error(f"SYNINT agent execution failed: {e}")
            self.observe({
                "type": "execution_failed",
                "error": str(e),
            })

            return {
                "status": "failed",
                "agent": self.name,
                "error": str(e),
                "observations": self.get_observation_buffer(),
            }

    def _run_synint_agent(self, cmd: List[str]) -> Dict[str, Any]:
        """
        Run SYNINT agent as a subprocess.

        Args:
            cmd: Command list to execute

        Returns:
            Dict with stdout and stderr

        Raises:
            subprocess.TimeoutExpired: If execution times out
            subprocess.CalledProcessError: If command fails with non-zero exit code
            RuntimeError: For other subprocess errors
        """
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            stdout, stderr = process.communicate(timeout=self.timeout_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            try:
                stdout, stderr = process.communicate()
            except Exception:  # cleanup only; the timeout is the real error
                stdout, stderr = "", ""
            raise subprocess.TimeoutExpired(
                cmd[0], self.timeout_seconds, output=stdout, stderr=stderr
            ) from None

        # A non-zero exit code is a failed command. Raise so that
        # _execute_with_retry retries it and so that failed output is never
        # stored as successful evidence.
        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode, cmd, output=stdout, stderr=stderr
            )

        return {
            "stdout": stdout,
            "stderr": stderr,
            "returncode": process.returncode,
        }

    def _parse_synint_result(self, result: Dict[str, str]) -> Dict[str, Any]:
        """
        Parse SYNINT agent output.

        Args:
            result: Dict with stdout and stderr

        Returns:
            Parsed result dict
        """
        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")

        # Try to parse JSON output
        if stdout.strip().startswith("{"):
            try:
                parsed = json.loads(stdout)
                return parsed
            except json.JSONDecodeError:
                pass

        # Fallback: extract claim from stdout
        claim = stdout.strip()[:500] if stdout.strip() else "No output"

        return {
            "claim": claim,
            "confidence": 0.7,  # Default confidence
            "independence_score": 0.8,
            "independence_check_details": {
                "financial_interest": False,
                "organizational_tie": False,
                "personal_relationship": False,
                "promotional_purpose": False,
            },
            "links": [],
            "sources": [
                f"SYNINT:{self.name}",
                {"stdout": stdout, "stderr": stderr}
            ],
        }

    def set_evidence_storage(self, storage: Any) -> None:
        """
        Set the evidence storage instance.

        Args:
            storage: SQLAlchemy session or ORM instance for evidence
        """
        super().set_evidence_storage(storage)
        self.db_session = storage  # Store for use in save_to_database


def main(argv: Optional[List[str]] = None) -> int:
    """
    Run one SYNINT agent from the command line and store its evidence.

    Returns process exit status: 0 on success, 1 on failure.
    """
    import argparse
    import os

    from sqlalchemy.orm import sessionmaker

    from ..database import create_db_engine, init_db
    from ..models.investigation import Investigation

    parser = argparse.ArgumentParser(
        prog="synint-wrapper",
        description="Execute a SYNINT agent and store its findings as evidence.",
    )
    parser.add_argument("--synint-path", required=True, help="Path to the SYNINT binary")
    parser.add_argument("--agent", default="WhoisAgent", help="SYNINT agent name")
    parser.add_argument("--target", required=True, help="Investigation target")
    parser.add_argument("--stage", default="standard", help="SYNINT stage")
    parser.add_argument(
        "--investigation-id", type=int, default=None, help="Existing investigation ID"
    )
    parser.add_argument(
        "--db-url",
        default=None,
        help="Database URL (defaults to DATABASE_URL or the local SQLite file)",
    )
    parser.add_argument("--timeout", type=int, default=300, help="Per-run timeout (s)")
    parser.add_argument("--max-retries", type=int, default=2, help="Retry attempts")
    args = parser.parse_args(argv)

    url = args.db_url or os.getenv("DATABASE_URL")
    engine = create_db_engine(url)
    init_db(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()

    try:
        investigation_id = args.investigation_id
        if investigation_id is None:
            investigation = Investigation(
                target_name=args.target,
                claim_under_investigation=f"SYNINT {args.agent} run for {args.target}",
                status="in_progress",
            )
            session.add(investigation)
            session.commit()
            investigation_id = investigation.id
        elif session.get(Investigation, investigation_id) is None:
            print(f"Investigation {investigation_id} not found")
            return 1

        wrapper = SYNINTAgentWrapper(
            synint_path=args.synint_path,
            name=args.agent,
            investigation_id=investigation_id,
            timeout_seconds=args.timeout,
            max_retries=args.max_retries,
        )
        wrapper.set_evidence_storage(session)

        result = wrapper.execute(
            {
                "agent_name": args.agent,
                "target": args.target,
                "stage": args.stage,
            }
        )
        print(json.dumps(result, indent=2, default=str))
        return 0 if result.get("status") == "success" else 1
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
