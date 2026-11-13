#!/usr/bin/env python3
"""Run verification from within the src/python directory."""

from agents.base import AgentBase
from agents.registry import AgentRegistry
from tools.base import ToolBase, ToolRegistry

print("Module imports successful")
print("- AgentBase:", AgentBase)
print("- ToolBase:", ToolBase)
print("- AgentRegistry:", AgentRegistry)
print("- ToolRegistry:", ToolRegistry)

# Test basic instantiation
agent = AgentBase(name="TestAgent", investigation_id=1, timeout_seconds=60)
print("\nAgentBase instantiated successfully")
print("- name:", agent.name)
print("- investigation_id:", agent.investigation_id)
print("- observation_buffer size:", len(agent.observation_buffer))

# Test observation
agent.observe({"type": "test"})
print("- observation_buffer after 1 observation:", len(agent.observation_buffer))

# Test tool instantiation
tool = ToolBase(name="TestTool", timeout_seconds=30)
print("\nToolBase instantiated successfully")
print("- name:", tool.name)
print("- timeout_seconds:", tool.timeout_seconds)

print("\n✅ All basic tests passed!")
