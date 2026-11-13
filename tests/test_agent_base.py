"""
Unit tests for Agent base class.
"""

from unittest.mock import Mock, patch

import pytest

from src.python.agents.base import AgentBase


class ConcreteAgent(AgentBase):
    """Minimal concrete subclass so AgentBase methods can be exercised."""

    def execute(self, context):
        return {"status": "success", "context": context}


class TestAgentBase:
    """Test suite for AgentBase class."""

    def test_agent_initialization(self):
        """Test agent initialization."""
        agent = ConcreteAgent(
            name="TestAgent",
            investigation_id=1,
            timeout_seconds=60,
        )

        assert agent.name == "TestAgent"
        assert agent.investigation_id == 1
        assert agent.timeout_seconds == 60
        assert agent.max_retries == 3
        assert agent.evidence_storage is None
        assert len(agent.observation_buffer) == 0

    def test_set_evidence_storage(self):
        """Test setting evidence storage."""
        mock_storage = Mock()
        agent = ConcreteAgent(name="TestAgent", investigation_id=1)

        agent.set_evidence_storage(mock_storage)
        assert agent.evidence_storage == mock_storage

    def test_observe(self):
        """Test observation recording."""
        agent = ConcreteAgent(name="TestAgent", investigation_id=1)

        agent.observe({"type": "test", "data": "sample"})

        assert len(agent.observation_buffer) == 1
        assert agent.observation_buffer[0]["type"] == "test"
        assert agent.observation_buffer[0]["agent"] == "TestAgent"
        assert "timestamp" in agent.observation_buffer[0]

    def test_get_observation_buffer(self):
        """Test getting observation buffer."""
        agent = ConcreteAgent(name="TestAgent", investigation_id=1)

        agent.observe({"type": "test1"})
        agent.observe({"type": "test2"})

        buffer = agent.get_observation_buffer()
        assert len(buffer) == 2
        assert buffer[0]["type"] == "test1"
        assert buffer[1]["type"] == "test2"

    def test_reset_observation_buffer(self):
        """Test resetting observation buffer."""
        agent = ConcreteAgent(name="TestAgent", investigation_id=1)

        agent.observe({"type": "test1"})
        agent.observe({"type": "test2"})
        assert len(agent.observation_buffer) == 2

        agent.reset_observation_buffer()
        assert len(agent.observation_buffer) == 0

    def test_format_confidence_high(self):
        """Test confidence formatting - High."""
        agent = ConcreteAgent(name="TestAgent", investigation_id=1)
        assert agent._format_confidence(0.8) == "High"

    def test_format_confidence_medium(self):
        """Test confidence formatting - Medium."""
        agent = ConcreteAgent(name="TestAgent", investigation_id=1)
        assert agent._format_confidence(0.6) == "Medium"

    def test_format_confidence_low(self):
        """Test confidence formatting - Low."""
        agent = ConcreteAgent(name="TestAgent", investigation_id=1)
        assert agent._format_confidence(0.3) == "Low"

    def test_store_evidence_without_storage(self):
        """Test storing evidence without storage set."""
        agent = ConcreteAgent(name="TestAgent", investigation_id=1)

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
        agent = ConcreteAgent(name="TestAgent", investigation_id=1)
        agent.set_evidence_storage(mock_storage)

        with patch("src.python.agents.base.Evidence") as mock_evidence_cls:
            mock_evidence_cls.return_value.id = 123
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
        agent = ConcreteAgent(name="TestAgent", investigation_id=1)

        with pytest.raises(ValueError, match="Evidence storage not initialized"):
            agent.update_confidence(1, 0.8, 0.9)

    def test_update_confidence_success(self):
        """Test successful confidence update."""
        mock_storage = Mock()
        mock_evidence = Mock()
        mock_storage.query.return_value.filter.return_value.first.return_value = mock_evidence

        agent = ConcreteAgent(name="TestAgent", investigation_id=1)
        agent.set_evidence_storage(mock_storage)

        agent.update_confidence(
            evidence_id=1,
            new_confidence=0.8,
            new_independence_score=0.95,
        )

        assert mock_evidence.confidence == 0.8
        assert mock_evidence.independence_score == 0.95
        mock_storage.commit.assert_called_once()

    def test_update_confidence_missing_entry(self):
        """Test updating confidence for a missing evidence entry."""
        mock_storage = Mock()
        mock_storage.query.return_value.filter.return_value.first.return_value = None

        agent = ConcreteAgent(name="TestAgent", investigation_id=1)
        agent.set_evidence_storage(mock_storage)

        with pytest.raises(ValueError, match="not found"):
            agent.update_confidence(99, 0.8, 0.9)

    def test_agent_base_is_abstract(self):
        """Test that AgentBase cannot be instantiated without execute()."""
        with pytest.raises(TypeError):
            AgentBase(name="TestAgent", investigation_id=1)  # type: ignore[abstract]

    def test_execute_with_retry_returns_first_success(self):
        """Test retry helper returns the first successful result."""
        agent = ConcreteAgent(name="TestAgent", investigation_id=1, max_retries=3)
        func = Mock(return_value={"status": "success"})

        assert agent._execute_with_retry(func) == {"status": "success"}
        assert func.call_count == 1

    def test_execute_with_retry_retries_then_raises(self):
        """Test retry helper retries failures and re-raises the last error."""
        agent = ConcreteAgent(name="TestAgent", investigation_id=1, max_retries=2)
        func = Mock(side_effect=RuntimeError("boom"))

        with patch("src.python.agents.base.time.sleep"):
            with pytest.raises(RuntimeError, match="boom"):
                agent._execute_with_retry(func)

        assert func.call_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
