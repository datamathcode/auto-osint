"""
Shared behaviour for OpenOSINT tool clients.
"""

import logging
import subprocess
from typing import Any, Dict, List, Optional

from ..base import RateLimitError, ToolBase

logger = logging.getLogger(__name__)

DEFAULT_RATE_LIMIT = {"requests_per_minute": 10}


class OpenOSINTClient(ToolBase):
    """
    Base class for OpenOSINT clients.

    Subclasses implement ``execute()``. This class supplies the CLI runner,
    the rate-limit gate, the result envelope, and database persistence.
    """

    tool_name: str = "openosint"
    source: str = "unknown"

    def __init__(
        self,
        name: Optional[str] = None,
        timeout_seconds: int = 60,
        rate_limit: Optional[Dict[str, int]] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        binary: Optional[str] = None,
    ):
        super().__init__(
            name=name or self.tool_name,
            timeout_seconds=timeout_seconds,
            rate_limit=rate_limit or dict(DEFAULT_RATE_LIMIT),
            max_retries=max_retries,
            retry_delay=retry_delay,
        )
        self.binary = binary or self.tool_name

    # -- persistence -----------------------------------------------------

    def set_db_session(self, session: Any) -> None:
        """Attach a SQLAlchemy session used by save_to_database()."""
        self.db_session = session

    def persist(self, result: Dict[str, Any], investigation_id: int) -> Optional[int]:
        """Store a result row and return its ID (None when it could not be saved)."""
        return self.save_to_database(result, investigation_id)

    # -- execution helpers -----------------------------------------------

    def result(
        self,
        status: str,
        target: str,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build the structured result envelope shared by all clients."""
        return {
            "status": status,
            "tool": self.tool_name,
            "target": target,
            "source": self.source,
            "data": data or {},
            "error": error,
        }

    def enforce_rate_limit(self) -> Optional[Dict[str, Any]]:
        """
        Apply the rate limit.

        Returns a failure envelope when the limit is hit, otherwise None.
        """
        try:
            self._check_rate_limit()
        except RateLimitError as exc:
            logger.warning(f"{self.name} rate limited: {exc}")
            return self.result("failed", "", error=str(exc))
        return None

    def run_binary(self, args: List[str]) -> str:
        """
        Run the client binary and return stdout.

        Raises:
            FileNotFoundError: binary is not installed
            subprocess.TimeoutExpired: run exceeded timeout_seconds
            RuntimeError: binary exited non-zero
        """
        command = [self.binary, *args]
        logger.info(f"{self.name} running: {' '.join(command)}")

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"{self.binary} is not installed or not on PATH") from exc

        if completed.returncode != 0:
            raise RuntimeError(
                f"{self.binary} exited {completed.returncode}: "
                f"{(completed.stderr or '').strip()[:200]}"
            )

        return completed.stdout

    def failure_from_exception(self, target: str, exc: Exception) -> Dict[str, Any]:
        """Convert an exception into a failed result with a readable error."""
        if isinstance(exc, FileNotFoundError):
            return self.result("failed", target, error=str(exc))
        if isinstance(exc, subprocess.TimeoutExpired):
            return self.result(
                "failed", target, error=f"{self.binary} timed out after {self.timeout_seconds}s"
            )
        return self.result("failed", target, error=str(exc))
