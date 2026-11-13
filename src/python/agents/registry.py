"""
Agent registry for auto-osint.
Provides registry pattern for agent discovery and management.
"""

import importlib
from typing import Dict, List, Optional, Type

from .base import AgentBase


class AgentRegistry:
    """
    Registry for managing agent classes.

    Agents can be registered here and discovered by name.
    """

    _registry: Dict[str, Type[AgentBase]] = {}

    @classmethod
    def register(cls, agent_class: Type[AgentBase]) -> None:
        """
        Register an agent class.

        Args:
            agent_class: Agent class to register
        """
        agent_name = agent_class.__name__
        cls._registry[agent_name] = agent_class
        print(f"Registered agent: {agent_name}")

    @classmethod
    def get_agent(cls, agent_name: str) -> Optional[Type[AgentBase]]:
        """
        Get a registered agent class by name.

        Args:
            agent_name: Name of the agent

        Returns:
            Agent class or None if not found
        """
        return cls._registry.get(agent_name)

    @classmethod
    def list_agents(cls) -> List[str]:
        """
        List all registered agent names.

        Returns:
            List of agent names
        """
        return list(cls._registry.keys())

    @classmethod
    def list_agents_with_info(cls) -> List[Dict[str, any]]:
        """
        List all registered agents with their descriptions.

        Returns:
            List of dicts with agent name and description
        """
        info = []
        for agent_name, agent_class in cls._registry.items():
            description = getattr(agent_class, "__doc__", "No description provided")
            info.append({
                "name": agent_name,
                "description": description.strip().split("\n")[0] if description else "No description provided",
            })
        return info

    @classmethod
    def register_from_config(cls, config_file: str) -> None:
        """
        Register agents from a configuration file.

        Args:
            config_file: Path to JSON/YAML config file

        Raises:
            ValueError: If config file not found or invalid
        """
        import json
        import os

        if not os.path.exists(config_file):
            raise ValueError(f"Config file not found: {config_file}")

        with open(config_file, "r") as f:
            config = json.load(f)

        for agent_name, agent_config in config.get("agents", {}).items():
            module_path = agent_config.get("module")
            class_name = agent_config.get("class")

            if not module_path or not class_name:
                raise ValueError(f"Invalid agent config for {agent_name}: missing module or class")

            try:
                # Import the module named in the config, then read the class.
                module = importlib.import_module(module_path)
                agent_class = getattr(module, class_name)

                # Register the agent
                cls.register(agent_class)
                print(f"Registered agent from config: {agent_name} ({module_path}.{class_name})")
            except ImportError as e:
                print(f"Failed to import agent {agent_name}: {e}")
            except AttributeError as e:
                print(f"Failed to get class {class_name} from module {module_path}: {e}")


# Auto-register all agent classes that inherit from AgentBase
# This happens automatically when modules are imported
def _auto_register_agents():
    """
    Auto-register all agents that inherit from AgentBase.
    This function is called when the module is imported.
    """
    for _agent_name in AgentRegistry.list_agents():
        # The actual registration happens when individual agents are imported
        # This is just a placeholder for the pattern
        pass


# Initialize the registry
if __name__ == "__main__":
    print("Agent registry initialized")
    print("Registered agents:", AgentRegistry.list_agents())
