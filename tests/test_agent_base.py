"""
Unit tests for Agent base class.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock

from src.python.agents.base import AgentBase


class TestAgentBase:
    """Test suite for AgentBase class."""

    def test_agent_initialization(self):
        """Test agent initialization."""
        mock_storage = Mock()
        agent = AgentBase(
            name="TestAgent",
            investigation_id=1,
            timeout_seconds=60,
        )
        
        assert agent.name == "TestAgent"
        assert agent.investigation_id == 1
        assert agent.timeout_seconds == 60
        assert agent.evidence_storage is None
        assert len(agent.observation_buffer) == 0

    def test_set_evidence_storage(self):
        """Test setting evidence storage."""
        mock_storage = Mock()
        agent = AgentBase(name="TestAgent", investigation_id=1)
        
        agent.set_evidence_storage(mock_storage)
        assert agent.evidence_storage == mock_storage

    def test_observe(self):
        """Test observation recording."""
        agent = AgentBase(name="TestAgent", investigation_id=1)
        
        agent.observe({"type": "test", "data": "sample"})
        
        assert len(agent.observation_buffer) == 1
        assert agent.observation_buffer[0]["type"] == "test"
        assert agent.observation_buffer[0]["agent"] == "TestAgent"
        assert "timestamp" in agent.observation_buffer[0]

    def test_get_observation_buffer(self):
        """Test getting observation buffer."""
        agent = AgentBase(name="TestAgent", investigation_id=1)
        
        agent.observe({"type": "test1"})
        agent.observe({"type": "test2"})
        
        buffer = agent.get_observation_buffer()
        assert len(buffer) == 2
        assert buffer[0]["type"] == "test1"
        assert buffer[1]["type"] == "test2"

    def test_reset_observation_buffer(self):
        """Test resetting observation buffer."""
        agent = AgentBase(name="TestAgent", investigation_id=1)
        
        agent.observe({"type": "test1"})
        agent.observe({"type": "test2"})
        
        assert len(agent.observation_buffer) == 2
        
        agent.reset_observation_buffer()
        assert len(agent.observation_buffer) == 0

    def test_format_confidence_high(self):
        """Test confidence formatting - High."""
        agent = AgentBase(name="TestAgent", investigation_id=1)
        assert agent._format_confidence(0.8) == "High"

    def test_format_confidence_medium(self):
        """Test confidence formatting - Medium."""
        agent = AgentBase(name="TestAgent", investigation_id=1)
        assert agent._format_confidence(0.6) == "Medium"

    def test_format_confidence_low(self):
        """Test confidence formatting - Low."""
        agent = AgentBase(name="TestAgent", investigation_id=1)
        assert agent._format_confidence(0.3) == "Low"

    def test_store_evidence_without_storage(self):
        """Test storing evidence without storage set."""
        agent = AgentBase(name="TestAgent", investigation_id=1)
        
        with pytest.raises(ValueError, match="Evidence storage not initialized"):
            agent.store_evidence(
                source="test",
                claim="test claim",
                confidence=0.7,
                independence_score=0.9,
            )

    def test_store_evidence_success(self):
        """Test successful evidence storage."""
        mock_storage = Mock()
        mock_evidence = Mock()
        mock_evidence.id = 123
        mock_storage.add.return_value = mock_evidence
        mock_storage.commit.return_value = None
        
        agent = AgentBase(name="TestAgent", investigation_id=1)
        agent.set_evidence_storage(mock_storage)
        
        evidence_id = agent.store_evidence(
            source="test",
            claim="test claim",
            confidence=0.7,
            independence_score=0.9,
        )
        
        assert evidence_id == 123
        mock_storage.add.assert_called_once()
        mock_storage.commit.assert_called_once()

    def test_update_confidence_without_storage(self):
        """Test updating confidence without storage set."""
        agent = AgentBase(name="TestAgent", investigation_id=1)
        
        with pytest.raises(ValueError, match="Evidence storage not initialized"):
            agent.update_confidence(1, 0.8, 0.9)

    def test_update_confidence_success(self):
        """Test successful confidence update."""
        mock_storage = Mock()
        mock_evidence = Mock()
        mock_storage.query.return_value.filter.return_value.first.return_value = mock_evidence
        mock_storage.commit.return_value = None
        
        agent = AgentBase(name="TestAgent", investigation_id=1)
        agent.set_evidence_storage(mock_storage)
        
        agent.update_confidence(
            evidence_id=1,
            new_confidence=0.8,
            new_independence_score=0.95,
        )
        
        assert mock_evidence.confidence == 0.8
        assert mock_evidence.independence_score == 0.95
        mock_storage.commit.assert_called_once()

    def test_execute_must_be_implemented(self):
        """Test that execute method must be implemented."""
        agent = AgentBase(name="TestAgent", investigation_id=1)
        
        with pytest.raises(NotImplementedError):
            agent.execute({"target": "example.com"})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
