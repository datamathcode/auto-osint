"""
Runtime configuration defaults.

Secrets are never returned: the client only learns whether a value is present.
"""

import os
from typing import Any, Dict

from fastapi import APIRouter

from ..database import database_url

router = APIRouter()

LLM_PROVIDERS = ["anthropic", "openai", "ollama"]


def _present(name: str) -> bool:
    return bool(os.getenv(name))


@router.get("/defaults")
def get_defaults() -> Dict[str, Any]:
    """Non-secret defaults for the investigation form."""
    return {
        "llm": {
            "provider": os.getenv("LLM_PROVIDER", "anthropic"),
            "providers": LLM_PROVIDERS,
            "model": os.getenv("OLLAMA_MODEL", ""),
            "has_api_key": _present("ANTHROPIC_API_KEY") or _present("OPENAI_API_KEY"),
            "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        },
        "openosint": {
            "has_breach_key": _present("HIBP_API_KEY"),
            "has_holehe_key": _present("HOLEHE_API_KEY"),
        },
        "synint": {"path": os.getenv("SYNINT_PATH", "synint")},
        "database": {"url": database_url(), "server_side": True},
        "limits": {
            "max_execution_time_seconds": int(os.getenv("MAX_EXECUTION_TIME", "3600")),
            "timeout_per_tool_seconds": int(os.getenv("TIMEOUT_PER_TOOL", "60")),
            "max_concurrent_queries": int(os.getenv("MAX_CONCURRENT_QUERIES", "8")),
        },
    }
