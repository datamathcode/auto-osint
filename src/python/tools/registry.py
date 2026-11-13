"""
Tool registry for auto-osint.
Provides registry pattern for tool discovery and management.
"""

import importlib
from typing import Dict, List, Optional, Type

from .base import ToolBase


class ToolRegistry:
    """
    Registry for managing tool classes.

    Tools can be registered here and discovered by name.
    """

    _registry: Dict[str, Type[ToolBase]] = {}

    @classmethod
    def register(cls, tool_class: Type[ToolBase]) -> None:
        """
        Register a tool class.

        Args:
            tool_class: Tool class to register
        """
        tool_name = tool_class.__name__
        cls._registry[tool_name] = tool_class
        print(f"Registered tool: {tool_name}")

    @classmethod
    def get_tool(cls, tool_name: str) -> Optional[Type[ToolBase]]:
        """
        Get a registered tool class by name.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool class or None if not found
        """
        return cls._registry.get(tool_name)

    @classmethod
    def list_tools(cls) -> List[str]:
        """
        List all registered tool names.

        Returns:
            List of tool names
        """
        return list(cls._registry.keys())

    @classmethod
    def list_tools_with_info(cls) -> List[Dict[str, any]]:
        """
        List all registered tools with their descriptions.

        Returns:
            List of dicts with tool name and description
        """
        info = []
        for tool_name, tool_class in cls._registry.items():
            description = getattr(tool_class, "__doc__", "No description provided")
            info.append({
                "name": tool_name,
                "description": description.strip().split("\n")[0] if description else "No description provided",
            })
        return info

    @classmethod
    def register_from_config(cls, config_file: str) -> None:
        """
        Register tools from a configuration file.

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

        for tool_name, tool_config in config.get("tools", {}).items():
            module_path = tool_config.get("module")
            class_name = tool_config.get("class")

            if not module_path or not class_name:
                raise ValueError(f"Invalid tool config for {tool_name}: missing module or class")

            try:
                # Import the module named in the config, then read the class.
                module = importlib.import_module(module_path)
                tool_class = getattr(module, class_name)

                # Register the tool
                cls.register(tool_class)
                print(f"Registered tool from config: {tool_name} ({module_path}.{class_name})")
            except ImportError as e:
                print(f"Failed to import tool {tool_name}: {e}")
            except AttributeError as e:
                print(f"Failed to get class {class_name} from module {module_path}: {e}")


# Auto-register all tool classes that inherit from ToolBase
# This happens automatically when modules are imported
def _auto_register_tools():
    """
    Auto-register all tools that inherit from ToolBase.
    This function is called when the module is imported.
    """
    for _tool_name in ToolRegistry.list_tools():
        # The actual registration happens when individual tools are imported
        # This is just a placeholder for the pattern
        pass


# Initialize the registry
if __name__ == "__main__":
    print("Tool registry initialized")
    print("Registered tools:", ToolRegistry.list_tools())
