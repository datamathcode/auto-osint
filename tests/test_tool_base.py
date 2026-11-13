"""
Unit tests for Tool base class.
"""

import pytest
import time
from unittest.mock import Mock, patch, call

from src.python.tools.base import ToolBase, RateLimitError


class TestToolBase:
    """Test suite for ToolBase class."""

    def test_tool_initialization(self):
        """Test tool initialization."""
        tool = ToolBase(
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
        tool = ToolBase(
            name="TestTool",
            rate_limit={"requests_per_minute": 60},
        )
        
        # First request should pass
        tool._check_rate_limit()
        
        # Subsequent request within same minute should pass
        tool._check_rate_limit()

    def test_tool_rate_limit_rejects(self):
        """Test rate limit is enforced."""
        tool = ToolBase(
            name="TestTool",
            rate_limit={"requests_per_minute": 1},
        )
        
        # First request passes
        tool._check_rate_limit()
        
        # Second request should fail
        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            tool._check_rate_limit()

    def test_tool_rate_limit_waits_before_retry(self):
        """Test tool waits before retrying after rate limit."""
        tool = ToolBase(
            name="TestTool",
            rate_limit={"requests_per_minute": 1},
            max_retries=2,
        )
        
        start_time = time.time()
        
        # First request passes
        tool._check_rate_limit()
        
        # Second request should fail immediately (waiting for next minute)
        with pytest.raises(RateLimitError):
            tool._check_rate_limit()
        
        elapsed = time.time() - start_time
        # Should be close to 60 seconds (rate limit window)
        assert elapsed > 55  # Allow some tolerance

    def test_execute_must_be_implemented(self):
        """Test that execute method must be implemented."""
        tool = ToolBase(name="TestTool")
        
        with pytest.raises(NotImplementedError):
            tool.execute("test_target")

    def test_log_result_success(self):
        """Test logging successful result."""
        tool = ToolBase(name="TestTool")
        result = {
            "status": "success",
            "data": {"result": "success"},
        }
        
        with patch("src.python.tools.base.logger") as mock_logger:
            tool.log_result(result)
            
            mock_logger.info.assert_any_call("TestTool completed successfully")
            mock_logger.info.assert_any_call("TestTool collected source: None")

    def test_log_result_failure(self):
        """Test logging failed result."""
        tool = ToolBase(name="TestTool")
        result = {
            "status": "failed",
            "error": "Operation failed",
        }
        
        with patch("src.python.tools.base.logger") as mock_logger:
            tool.log_result(result)
            
            mock_logger.error.assert_any_call("TestTool failed: Operation failed")

    def test_save_to_database_no_session(self):
        """Test saving to database when session not available."""
        tool = ToolBase(name="TestTool")
        
        # Simulate no db_session attribute
        delattr(tool, "db_session")
        
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
        tool = ToolBase(name="TestTool")
        tool.db_session = Mock()
        
        result = {
            "status": "success",
            "target": "example.com",
            "data": {"key": "value"},
        }
        
        mock_result = Mock()
        mock_result.id = 456
        tool.db_session.add.return_value = mock_result
        tool.db_session.commit.return_value = None
        
        saved_id = tool.save_to_database(
            result=result,
            investigation_id=1,
        )
        
        assert saved_id == 456
        tool.db_session.add.assert_called_once()
        tool.db_session.commit.assert_called_once()


class TestToolBaseWithRetry:
    """Test suite for ToolBase retry logic."""

    def test_execute_with_retry_success(self):
        """Test execute succeeds on first try."""
        tool = ToolBase(name="TestTool", max_retries=2)
        
        # Mock function that succeeds
        mock_func = Mock(return_value={"status": "success"})
        
        result = tool._execute_with_retry(mock_func, "arg1", "arg2")
        
        assert result == {"status": "success"}
        mock_func.assert_called_once_with("arg1", "arg2")

    def test_execute_with_retry_fails_on_last_retry(self):
        """Test execute fails after all retries."""
        tool = ToolBase(name="TestTool", max_retries=3, retry_delay=0.1)
        
        # Mock function that always fails
        mock_func = Mock(side_effect=Exception("Simulated failure"))
        
        with pytest.raises(RuntimeError, match="after 3 retries"):
            tool._execute_with_retry(mock_func)
        
        # Should be called max_retries times
        assert mock_func.call_count == 3

    def test_execute_with_retry_exponential_backoff(self):
        """Test execute uses exponential backoff."""
        tool = ToolBase(name="TestTool", max_retries=3, retry_delay=0.1)
        
        # Mock function that always fails
        mock_func = Mock(side_effect=Exception("Simulated failure"))
        
        with patch("src.python.tools.base.time.sleep") as mock_sleep:
            with pytest.raises(RuntimeError):
                tool._execute_with_retry(mock_func)
            
            # Check that sleep was called with exponential delays
            # 0.1 * 2^0 = 0.1, 0.1 * 2^1 = 0.2, 0.1 * 2^2 = 0.4
            sleep_calls = [call(args) for args in mock_sleep.call_args_list]
            assert len(sleep_calls) == 2
            # First call after first failure (2 retries left)
            assert sleep_calls[0] == call(0.1)
            # Second call after second failure (1 retry left)
            assert sleep_calls[1] == call(0.2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
