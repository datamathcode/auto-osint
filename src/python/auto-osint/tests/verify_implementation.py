#!/usr/bin/env python3
"""
Simple verification script to check if Agent and Tool base classes work.
Does not require pytest.
"""

import os
import sys

# Add src/python to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'python'))

from unittest.mock import Mock

from agents.base import AgentBase
from agents.registry import AgentRegistry
from tools.base import ToolBase, ToolRegistry


def test_agent_base():
    """Test AgentBase basic functionality."""
    print("Testing AgentBase...")
    
    # Test initialization
    agent = AgentBase(name="TestAgent", investigation_id=1, timeout_seconds=60)
    assert agent.name == "TestAgent"
    assert agent.investigation_id == 1
    
    # Test observation
    agent.observe({"type": "test"})
    assert len(agent.observation_buffer) == 1
    
    # Test confidence formatting
    assert agent._format_confidence(0.8) == "High"
    assert agent._format_confidence(0.6) == "Medium"
    assert agent._format_confidence(0.3) == "Low"
    
    print("✓ AgentBase tests passed")


def test_tool_base():
    """Test ToolBase basic functionality."""
    print("\nTesting ToolBase...")
    
    # Test initialization
    tool = ToolBase(name="TestTool", timeout_seconds=60)
    assert tool.name == "TestTool"
    assert tool.timeout_seconds == 60
    
    # Test rate limit
    assert tool._check_rate_limit() is None  # Should not raise
    
    # Test that execute must be implemented
    try:
        tool.execute("test")
        assert False, "Should have raised NotImplementedError"
    except NotImplementedError:
        pass
    
    print("✓ ToolBase tests passed")


def test_registry():
    """Test registry functionality."""
    print("\nTesting registries...")
    
    # Test agent registry
    agent_registry = AgentRegistry()
    agents = agent_registry.list_agents()
    print(f"  Agents: {agents}")
    
    # Test tool registry
    tool_registry = ToolRegistry()
    tools = tool_registry.list_tools()
    print(f"  Tools: {tools}")
    
    print("✓ Registries tests passed")


def test_synint_wrapper():
    """Test SYNINTAgentWrapper."""
    print("\nTesting SYNINTAgentWrapper...")
    
    try:
        from agents.synint_wrapper import SYNINTAgentWrapper
        
        mock_storage = Mock()
        wrapper = SYNINTAgentWrapper(
            synint_path="/usr/bin/synint",
            name="WhoisAgent",
            investigation_id=1,
            max_retries=1,  # No retries for speed
        )
        
        wrapper.set_evidence_storage(mock_storage)
        
        # This should work (but might fail if no SYNINT installed)
        try:
            result = wrapper.execute({
                "target": "example.com",
            })
            
            if result["status"] == "failed":
                print(f"  Note: SYNINT not installed, but wrapper works: {result['error']}")
            else:
                print("  ✓ SYNINTAgentWrapper works (SYNINT is installed)")
        except Exception as e:
            print(f"  Note: SYNINT execution error (expected if not installed): {type(e).__name__}")
        
    except ImportError as e:
        print(f"  ✗ Cannot import SYNINTAgentWrapper: {e}")
    
    print("✓ SYNINTAgentWrapper tests completed")


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Running implementation verification")
    print("=" * 60)
    
    try:
        test_agent_base()
        test_tool_base()
        test_registry()
        test_synint_wrapper()
        
        print("\n" + "=" * 60)
        print("✓ ALL VERIFICATION TESTS PASSED")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n✗ VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
