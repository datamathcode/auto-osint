"""
Mock SYNINT agent for testing purposes.

This is a simple agent that simulates SYNINT behavior for testing
the agent framework without requiring SYNINT to be installed.
"""

import logging
from typing import Any, Dict

from ..base import AgentBase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockSYNINTAgent(AgentBase):
    """
    Mock SYNINT agent for testing the framework.

    This agent simulates a simple OSINT operation and can be used
    to test the agent framework without a real SYNINT installation.
    """

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a mock SYNINT operation.

        Args:
            context: Investigation context with target info

        Returns:
            Dict with execution results
        """
        self.reset_observation_buffer()
        self.observe({"type": "execution_started", "context": context})

        target = context.get("target", "example.com")
        agent_name = context.get("agent_name", "MockSYNINTAgent")

        # Simulate work
        self.observe({"type": "simulated_discovery", "target": target})

        # Store sample evidence
        evidence_id = self.store_evidence(
            source=f"MockSYNINT:{agent_name}",
            claim=f"Found information about {target}",
            confidence=0.8,
            independence_score=0.9,
            links=[f"https://example.com/{target}"],
            chain_of_custody=[{
                "timestamp": "mock_timestamp",
                "discovery_type": "mock",
            }],
        )

        self.observe({
            "type": "evidence_stored",
            "evidence_id": evidence_id,
        })

        logger.info(f"Mock SYNINT agent completed for {target}")

        return {
            "status": "success",
            "agent": agent_name,
            "target": target,
            "result": {
                "data": {
                    "description": f"Mock information about {target}",
                    "confidence": "High",
                    "sources": ["mock_synint_output"],
                }
            },
            "evidence_id": evidence_id,
            "observations": self.get_observation_buffer(),
        }
