"""
Email search client (holehe or an equivalent CLI).

Structured result shape:
    data = {"email": str, "platforms_found": [{"platform": str, "url": str}],
            "count": int, "raw": str}
"""

import logging
import re
from typing import Any, Dict, List, Optional

from .base import OpenOSINTClient

logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(r"https?://[^\s\]\)\"']+")
PLATFORM_PATTERN = re.compile(r"^\[\+\]\s*(.+)$")


def parse_holehe_output(stdout: str) -> List[Dict[str, Any]]:
    """
    Extract platforms and URLs from holehe's text output.

    holehe prints one block per site, marking hits with "[+]". Lines without a
    URL still count as a hit, so the platform is recorded with an empty url.
    """
    found: List[Dict[str, Any]] = []
    current_platform: Optional[str] = None

    for line in stdout.splitlines():
        stripped = line.strip()
        match = PLATFORM_PATTERN.match(stripped)
        if match:
            current_platform = match.group(1).strip()
            urls = URL_PATTERN.findall(stripped)
            found.append({"platform": current_platform, "url": urls[0] if urls else ""})
            continue

        urls = URL_PATTERN.findall(stripped)
        if urls and current_platform:
            # Attach the first URL seen for the most recent hit.
            if not found[-1]["url"]:
                found[-1]["url"] = urls[0]

    return found


class SearchEmailClient(OpenOSINTClient):
    """Look up which services an email address is registered with."""

    tool_name = "search_email"
    source = "holehe"

    def execute(self, target: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run the email search and return structured findings."""
        if not target:
            return self.result("failed", target, error="email is required")
        if "@" not in target:
            return self.result("failed", target, error=f"invalid email address: {target}")

        limited = self.enforce_rate_limit()
        if limited is not None:
            limited["target"] = target
            return limited

        try:
            stdout = self.run_binary([target])
        except Exception as exc:
            return self.failure_from_exception(target, exc)

        platforms = parse_holehe_output(stdout)
        status = "success" if platforms else "partial"
        return self.result(
            status,
            target,
            data={
                "email": target,
                "platforms_found": platforms,
                "count": len(platforms),
                "raw": stdout.strip()[:2000],
            },
            error=None if platforms else "no platforms detected in tool output",
        )
