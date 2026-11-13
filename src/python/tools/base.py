"""
Base Tool class for auto-osint.
Provides common functionality for tool execution including timeout enforcement,
rate limiting, and error handling.
"""

import asyncio
import logging
import signal
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models.openosint_result import OpenOSINTResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ToolBase(ABC):
    """
    Base tool class with common execution lifecycle methods.

    Tools can be specialized by subclassing this class and implementing
    the specific tool execution method.
    """

    def __init__(
        self,
        name: str,
        timeout_seconds: int = 60,
        rate_limit: Optional[Dict[str, int]] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize the tool.

        Args:
            name: Tool name for logging and registry
            timeout_seconds: Maximum execution time for tool invocation
            rate_limit: Rate limiting config: {'requests_per_minute': int}
            max_retries: Maximum number of retry attempts for failed operations
            retry_delay: Base delay between retries (exponential backoff applied)
        """
        self.name = name
        self.timeout_seconds = timeout_seconds
        self.rate_limit = rate_limit or {"requests_per_minute": 60}
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.last_request_time = 0
        self._request_times: List[float] = []

    @abstractmethod
    def execute(self, target: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the tool's primary function.

        This method should be implemented by specific tool types.
        It should define the actual OSINT tool logic.

        Args:
            target: Target identifier (e.g., domain, username, IP address)
            params: Additional parameters for the tool execution

        Returns:
            Dict with results, status, and metadata
        """
        pass

    def _check_rate_limit(self) -> None:
        """
        Check if the current request is within rate limits.

        Raises:
            RateLimitError: If rate limit would be exceeded
        """
        if not self.rate_limit:
            return

        requests_per_minute = self.rate_limit.get("requests_per_minute", 60)
        if requests_per_minute <= 0:
            return

        now = time.time()
        window_start = now - 60

        # Keep only requests inside the current 60 second window.
        self._request_times = [t for t in self._request_times if t > window_start]

        if len(self._request_times) >= requests_per_minute:
            oldest = min(self._request_times)
            wait_time = 60 - (now - oldest)
            raise RateLimitError(
                f"Rate limit exceeded. Waiting {wait_time:.1f}s until next window."
            )

        self._request_times.append(now)
        self.last_request_time = now
        logger.info(f"{self.name} rate limit check passed")

    def _execute_with_timeout(self, coro) -> Dict[str, Any]:
        """
        Execute a coroutine with timeout enforcement.

        Args:
            coro: Async coroutine to execute

        Returns:
            Execution results

        Raises:
            TimeoutError: If execution exceeds timeout_seconds
        """
        def timeout_handler(signum, frame):
            raise TimeoutError(f"{self.name} execution timed out after {self.timeout_seconds}s")

        try:
            # Set timeout for synchronous code that might block
            # Note: This only works on Unix-like systems
            if hasattr(signal, "SIGALRM"):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(self.timeout_seconds)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(coro)
            loop.close()

            if hasattr(signal, "SIGALRM"):
                signal.alarm(0)  # Cancel the alarm

            return result
        except TimeoutError:
            logger.error(f"{self.name} timed out")
            raise
        finally:
            if hasattr(signal, "SIGALRM"):
                signal.alarm(0)  # Ensure alarm is canceled

    def _execute_with_retry(self, func, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute function with exponential backoff retries.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Execution results

        Raises:
            RuntimeError: If all retries fail
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                logger.info(f"{self.name} attempt {attempt + 1}/{self.max_retries}")
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"{self.name} attempt {attempt + 1} failed: {e}. Retrying in {wait_time:.1f}s")
                    time.sleep(wait_time)

        logger.error(f"{self.name} all {self.max_retries} retries failed")
        raise RuntimeError(f"{self.name} execution failed after {self.max_retries} retries: {last_exception}")

    def log_result(self, result: Dict[str, Any]) -> None:
        """
        Log tool execution result.

        Args:
            result: Result dict with status, error, and data
        """
        status = result.get("status", "unknown")
        error = result.get("error")
        source = result.get("source")

        if status == "success":
            logger.info(f"{self.name} completed successfully")
            if source:
                logger.info(f"{self.name} collected source: {source}")
        else:
            logger.error(f"{self.name} failed: {error}")

    def save_to_database(
        self,
        result: Dict[str, Any],
        investigation_id: int,
        tool: Optional[str] = None,
    ) -> Optional[int]:
        """
        Save tool results to database.

        Args:
            result: Result dict from tool execution
            investigation_id: Associated investigation ID
            tool: Tool name (defaults to self.name)

        Returns:
            ID of saved result or None if error

        Raises:
            ValueError: If database session not available
        """
        if not hasattr(self, "db_session"):
            logger.warning(f"{self.name} database session not available")
            return None

        tool_name = tool or self.name
        tool_result = OpenOSINTResult(
            tool=tool_name,
            target=result.get("target", ""),
            result=result.get("data", {}),
            source=result.get("source"),
            timestamp=datetime.utcnow(),
            error=result.get("error"),
            investigation_id=investigation_id,
        )

        self.db_session.add(tool_result)
        self.db_session.commit()
        result_id = tool_result.id

        logger.info(f"{self.name} saved result ID {result_id} to database")
        return result_id


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""
    pass
