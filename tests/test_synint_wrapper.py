"""
Integration test for SYNINT agent wrapper.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from unittest.mock.mock import AsyncMock

from src.python.agents.synint_wrapper import SYNINTAgentWrapper


class TestSYNINTAgentWrapper:
    """Test suite for SYNINTAgentWrapper class."""

    def test_synint_wrapper_initialization(self):
        """Test SYNINT agent wrapper initialization."""
        mock_storage = Mock()
        wrapper = SYNINTAgentWrapper(
            synint_path="/usr/bin/synint",
            name="WhoisAgent",
            investigation_id=1,
            timeout_seconds=60,
        )
        
        assert wrapper.synint_path == "/usr/bin/synint"
        assert wrapper.name == "WhoisAgent"
        assert wrapper.investigation_id == 1

    def test_execute_requires_target(self):
        """Test execute requires target in context."""
        wrapper = SYNINTAgentWrapper(
            synint_path="/usr/bin/synint",
            name="WhoisAgent",
            investigation_id=1,
        )
        
        with pytest.raises(ValueError, match="Target must be provided"):
            wrapper.execute({})

    def test_execute_stores_evidence(self):
        """Test that execute stores evidence."""
        mock_storage = Mock()
        mock_evidence = Mock()
        mock_evidence.id = 123
        mock_storage.add.return_value = mock_evidence
        mock_storage.commit.return_value = None
        
        wrapper = SYNINTAgentWrapper(
            synint_path="/usr/bin/synint",
            name="WhoisAgent",
            investigation_id=1,
        )
        wrapper.set_evidence_storage(mock_storage)
        
        result = wrapper.execute({
            "target": "example.com",
            "agent_name": "WhoisAgent",
            "stage": "standard",
        })
        
        # Check that evidence was stored
        assert result["status"] == "success"
        assert result["evidence_id"] == 123
        
        # Check that evidence was saved with correct parameters
        call_args = mock_storage.add.call_args[0][0]
        assert call_args.source == "SYNINT:WhoisAgent"
        assert "example.com" in call_args.claim.lower()

    def test_execute_fails_on_synint_error(self):
        """Test that execute handles SYNINT errors."""
        wrapper = SYNINTAgentWrapper(
            synint_path="/usr/bin/synint",
            name="WhoisAgent",
            investigation_id=1,
            max_retries=0,  # No retries for this test
        )
        wrapper.set_evidence_storage(Mock())
        
        # Mock subprocess to fail
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.side_effect = Exception("SYNINT failed")
            mock_popen.return_value = mock_process
            
            result = wrapper.execute({
                "target": "example.com",
            })
            
            assert result["status"] == "failed"
            assert "SYNINT agent execution failed" in result["error"]

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
        
        parsed = SYNINTAgentWrapper._parse_synint_result(result)
        
        assert parsed["claim"] == "Domain example.com registered to John Doe"
        assert parsed["confidence"] == 0.85
        assert "sources" in parsed["data"]

    def test_parse_synint_result_fallback(self):
        """Test fallback parsing when output is not JSON."""
        result = {
            "stdout": "Some raw output from SYNINT\nMore lines here",
            "stderr": "",
        }
        
        parsed = SYNINTAgentWrapper._parse_synint_result(result)
        
        assert parsed["claim"].startswith("Some raw output from SYNINT")
        assert parsed["confidence"] == 0.7  # Default confidence

    def test_execute_with_timeout(self):
        """Test that SYNINT execution respects timeout."""
        wrapper = SYNINTAgentWrapper(
            synint_path="/usr/bin/synint",
            name="WhoisAgent",
            investigation_id=1,
            timeout_seconds=1,  # Short timeout
        )
        
        # Mock subprocess that hangs
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.side_effect = Exception("Timeout")
            mock_popen.return_value = mock_process
            
            wrapper.set_evidence_storage(Mock())
            
            with pytest.raises(TimeoutError, match="timed out"):
                wrapper.execute({
                    "target": "example.com",
                })


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
