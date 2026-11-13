"""
SYNINT agent shell wrapper for auto-osint.

This module provides a wrapper that executes SYNINT agents from the command line
and stores results as evidence in the database.
"""

import json
import logging
import subprocess
from typing import Any, Dict, List

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
