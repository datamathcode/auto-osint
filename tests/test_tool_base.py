"""
Unit tests for Tool base class.
"""

import time
from unittest.mock import Mock, call, patch

import pytest

from src.python.tools.base import RateLimitError, ToolBase


class ConcreteTool(ToolBase):
    """Minimal concrete subclass so ToolBase methods can be exercised."""

    def execute(self, target, params=None):
        return {"status": "success", "target": target, "data": params or {}}


class TestToolBase:
    """Test suite for ToolBase class."""

    def test_tool_initialization(self):
        """Test tool initialization."""
        tool = ConcreteTool(
            name="TestTool",
            timeout_seconds=60,
            rate_limit={"requests_per_minute": 60},
        )

        assert tool.name == "TestTool"
        assert tool.timeout_seconds == 60
        assert tool.rate_limit == {"requests_per_minute": 60}
        assert tool.max_retries == 3
        assert tool.last_request_time == 0

    def test_tool_rate_limit_check_passes(self):
        """Test rate limit check passes when within limits."""
        tool = ConcreteTool(
            name="TestTool",
            rate_limit={"requests_per_minute": 60},
        )

        tool._check_rate_limit()
        tool._check_rate_limit()

    def test_tool_rate_limit_rejects(self):
        """Test rate limit is enforced once the window is full."""
        tool = ConcreteTool(
            name="TestTool",
            rate_limit={"requests_per_minute": 1},
        )

        tool._check_rate_limit()

        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            tool._check_rate_limit()

    def test_tool_rate_limit_raises_without_blocking(self):
        """Test the rate limit check fails fast instead of sleeping."""
        tool = ConcreteTool(
            name="TestTool",
            rate_limit={"requests_per_minute": 1},
        )

        start_time = time.time()
        tool._check_rate_limit()

        with pytest.raises(RateLimitError):
            tool._check_rate_limit()

        elapsed = time.time() - start_time
        assert elapsed < 5

    def test_tool_execute_must_be_implemented(self):
        """Test that ToolBase cannot be instantiated without execute()."""
        with pytest.raises(TypeError):
            ToolBase(name="TestTool")  # type: ignore[abstract]

    def test_log_result_success(self):
        """Test logging successful result."""
        tool = ConcreteTool(name="TestTool")
        result = {
            "status": "success",
            "data": {"result": "success"},
        }

        with patch("src.python.tools.base.logger") as mock_logger:
            tool.log_result(result)

            mock_logger.info.assert_any_call("TestTool completed successfully")

    def test_log_result_failure(self):
        """Test logging failed result."""
        tool = ConcreteTool(name="TestTool")
        result = {
            "status": "failed",
            "error": "Operation failed",
        }

        with patch("src.python.tools.base.logger") as mock_logger:
            tool.log_result(result)

            mock_logger.error.assert_any_call("TestTool failed: Operation failed")

    def test_save_to_database_no_session(self):
        """Test saving to database when session not available."""
        tool = ConcreteTool(name="TestTool")

        result = {
            "status": "success",
            "data": {},
        }

        saved_id = tool.save_to_database(
            result=result,
            investigation_id=1,
        )

        assert saved_id is None

    def test_save_to_database_success(self):
        """Test successful database save."""
        tool = ConcreteTool(name="TestTool")
        tool.db_session = Mock()  # type: ignore[attr-defined]

        result = {
            "status": "success",
            "target": "example.com",
            "data": {"key": "value"},
        }

        with patch("src.python.tools.base.OpenOSINTResult") as mock_result_cls:
            mock_result_cls.return_value.id = 456
            saved_id = tool.save_to_database(
                result=result,
                investigation_id=1,
            )

        assert saved_id == 456
        tool.db_session.add.assert_called_once()  # type: ignore[attr-defined]
        tool.db_session.commit.assert_called_once()  # type: ignore[attr-defined]


class TestToolBaseWithRetry:
    """Test suite for ToolBase retry logic."""

    def test_execute_with_retry_success(self):
        """Test execute succeeds on first try."""
        tool = ConcreteTool(name="TestTool", max_retries=2)

        mock_func = Mock(return_value={"status": "success"})

        result = tool._execute_with_retry(mock_func, "arg1", "arg2")

        assert result == {"status": "success"}
        mock_func.assert_called_once_with("arg1", "arg2")

    def test_execute_with_retry_fails_on_last_retry(self):
        """Test execute fails after all retries."""
        tool = ConcreteTool(name="TestTool", max_retries=3, retry_delay=0.1)

        mock_func = Mock(side_effect=Exception("Simulated failure"))

        with patch("src.python.tools.base.time.sleep"):
            with pytest.raises(RuntimeError, match="after 3 retries"):
                tool._execute_with_retry(mock_func)

        assert mock_func.call_count == 3

    def test_execute_with_retry_exponential_backoff(self):
        """Test execute uses exponential backoff."""
        tool = ConcreteTool(name="TestTool", max_retries=3, retry_delay=0.1)

        mock_func = Mock(side_effect=Exception("Simulated failure"))

        with patch("src.python.tools.base.time.sleep") as mock_sleep:
            with pytest.raises(RuntimeError):
                tool._execute_with_retry(mock_func)

            sleep_calls = mock_sleep.call_args_list
            assert len(sleep_calls) == 2
            assert sleep_calls[0] == call(0.1)
            assert sleep_calls[1] == call(0.2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
