"""
Registry tests: the JSON config must load real classes through the real loader.
"""

from pathlib import Path

from src.python.agents.registry import AgentRegistry
from src.python.tools.registry import ToolRegistry

AGENTS_CONFIG = Path("src/python/agents/config.json")
TOOLS_CONFIG = Path("src/python/tools/config.json")


class TestAgentRegistryConfig:
    def test_config_registers_real_agent_classes(self):
        AgentRegistry._registry.clear()

        AgentRegistry.register_from_config(str(AGENTS_CONFIG))

        assert "SYNINTAgentWrapper" in AgentRegistry.list_agents()
        assert "MockSYNINTAgent" in AgentRegistry.list_agents()


class TestToolRegistryConfig:
    def test_config_registers_real_tool_classes(self):
        ToolRegistry._registry.clear()

        ToolRegistry.register_from_config(str(TOOLS_CONFIG))

        tools = ToolRegistry.list_tools()
        assert "MockDomainLookupTool" in tools

        tool_class = ToolRegistry.get_tool("MockDomainLookupTool")
        assert tool_class is not None
        instance = tool_class(rate_limit={"requests_per_minute": 0})
        result = instance.execute("example.com")

        assert result["status"] == "success"
        assert result["data"]["registrar"] == "Example Registrar"
