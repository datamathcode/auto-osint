"""
Username search client (sherlock or an equivalent CLI).

Structured result shape:
    data = {"username": str, "platforms_found": [{"platform": str, "url": str}],
            "count": int, "raw": str}
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from .base import OpenOSINTClient

logger = logging.getLogger(__name__)


def parse_sherlock_output(stdout: str) -> List[Dict[str, Any]]:
    """
    Normalise sherlock-style JSON into [{platform, url}].

    Accepts the documented shapes: {site: url}, {site: {"url": ...}},
    {"sites": {...}} and [{site/name, url}]. Returns [] when the output is
    not JSON, so the caller can report a partial result instead of failing.
    """
    text = stdout.strip()
    if not text:
        return []

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("search_username: output was not JSON; returning no platforms")
        return []

    if isinstance(payload, dict) and "sites" in payload and isinstance(payload["sites"], (dict, list)):
        payload = payload["sites"]

    found: List[Dict[str, Any]] = []

    if isinstance(payload, dict):
        for site, value in payload.items():
            if isinstance(value, str):
                found.append({"platform": site, "url": value})
            elif isinstance(value, dict):
                url = value.get("url") or value.get("url_main") or value.get("url_user")
                if url:
                    found.append({"platform": site, "url": url})
    elif isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                url = item.get("url") or item.get("url_user")
                platform = item.get("site") or item.get("name") or item.get("platform")
                if url and platform:
                    found.append({"platform": platform, "url": url})

    return found


SHERLOCK_LINE = re.compile(r"^\[\+\]\s*([^:]+):\s*(https?://\S+)")


def parse_sherlock_text(stdout: str) -> List[Dict[str, Any]]:
    """Parse sherlock's human-readable output: `[+] GitHub: https://...`.

    Current sherlock releases have no JSON output mode (`--json` loads site
    definitions from a file), so this parser is the real-world path.
    """
    found: List[Dict[str, Any]] = []
    for line in stdout.splitlines():
        match = SHERLOCK_LINE.match(line.strip())
        if match:
            found.append({"platform": match.group(1).strip(), "url": match.group(2).strip()})
    return found


class SearchUsernameClient(OpenOSINTClient):
    """Look up a username across public sites."""

    tool_name = "search_username"
    source = "sherlock"

    def execute(self, target: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run the username search and return structured findings."""
        if not target:
            return self.result("failed", target, error="username is required")

        limited = self.enforce_rate_limit()
        if limited is not None:
            limited["target"] = target
            return limited

        try:
            timeout = os.getenv("SHERLOCK_TIMEOUT", "10")
            stdout = self.run_binary(
                [target, "--print-found", "--no-color", "--timeout", timeout]
            )
        except Exception as exc:  # binary missing, timeout, non-zero exit
            return self.failure_from_exception(target, exc)

        platforms = parse_sherlock_output(stdout) or parse_sherlock_text(stdout)
        status = "success" if platforms else "partial"
        return self.result(
            status,
            target,
            data={
                "username": target,
                "platforms_found": platforms,
                "count": len(platforms),
                "raw": stdout.strip()[:2000],
            },
            error=None if platforms else "no platforms detected in tool output",
        )
