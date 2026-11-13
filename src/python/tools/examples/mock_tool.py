"""
Deterministic example tool.

Returns canned registration data so the tool pipeline, registry, and evidence
storage can be exercised without network access.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ..base import ToolBase


class MockDomainLookupTool(ToolBase):
    """Return canned registrar data for a domain."""

    def __init__(self, **kwargs):
        kwargs.setdefault("name", "MockDomainLookupTool")
        super().__init__(**kwargs)

    def execute(self, target: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Return a fixed registration record for the target."""
        if not target:
            return {"status": "failed", "target": target, "error": "target is required"}

        return {
            "status": "success",
            "target": target,
            "source": "mock://domain-lookup",
            "data": {
                "domain": target,
                "registrar": "Example Registrar",
                "registered_at": "2020-01-01",
                "checked_at": datetime.now(timezone.utc).isoformat(),
            },
        }
