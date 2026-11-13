"""
Breach lookup client for the Have I Been Pwned v3 API.

Structured result shape:
    data = {"email": str, "breaches": [{"name": str, "domain": str,
            "breach_date": str, "data_classes": [str]}], "count": int}
"""

import logging
import os
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests

from .base import OpenOSINTClient

logger = logging.getLogger(__name__)

HIBP_URL = "https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
USER_AGENT = "auto-osint"


class SearchBreachClient(OpenOSINTClient):
    """Check whether an email appears in known breaches (HIBP)."""

    tool_name = "search_breach"
    source = "haveibeenpwned"

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_key_env: str = "HIBP_API_KEY",
        base_url: str = HIBP_URL,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._api_key = api_key
        self.api_key_env = api_key_env
        self.base_url = base_url

    @property
    def api_key(self) -> Optional[str]:
        """Resolve the API key from the constructor or the environment."""
        return self._api_key or os.getenv(self.api_key_env)

    def _parse_breaches(self, payload: Any) -> List[Dict[str, Any]]:
        breaches: List[Dict[str, Any]] = []
        if not isinstance(payload, list):
            return breaches

        for item in payload:
            if not isinstance(item, dict):
                continue
            breaches.append(
                {
                    "name": item.get("Name"),
                    "domain": item.get("Domain"),
                    "breach_date": item.get("BreachDate"),
                    "data_classes": item.get("DataClasses") or [],
                }
            )
        return breaches

    def execute(self, target: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Query HIBP for breaches affecting the email address."""
        if not target:
            return self.result("failed", target, error="email is required")
        if "@" not in target:
            return self.result("failed", target, error=f"invalid email address: {target}")

        limited = self.enforce_rate_limit()
        if limited is not None:
            limited["target"] = target
            return limited

        api_key = self.api_key
        if not api_key:
            return self.result(
                "failed",
                target,
                error=f"{self.api_key_env} is not set; cannot query HIBP",
            )

        headers = {"hibp-api-key": api_key, "user-agent": USER_AGENT}
        url = self.base_url.format(email=quote(target, safe=""))

        try:
            response = requests.get(
                url, headers=headers, timeout=self.timeout_seconds
            )
        except requests.Timeout:
            return self.result(
                "failed", target, error=f"HIBP request timed out after {self.timeout_seconds}s"
            )
        except requests.RequestException as exc:
            logger.error(f"search_breach request failed: {exc}")
            return self.result("failed", target, error=str(exc))

        if response.status_code == 404:
            # Documented "no breaches found" answer, not an error.
            return self.result(
                "success",
                target,
                data={"email": target, "breaches": [], "count": 0},
            )

        if response.status_code == 401:
            return self.result("failed", target, error="HIBP rejected the API key (401)")
        if response.status_code == 429:
            retry_after = response.headers.get("retry-after", "unknown")
            return self.result(
                "failed",
                target,
                error=f"HIBP rate limit hit (429), retry after {retry_after}s",
            )
        if response.status_code >= 400:
            return self.result(
                "failed",
                target,
                error=f"HIBP returned HTTP {response.status_code}",
            )

        try:
            payload = response.json()
        except ValueError:
            return self.result("partial", target, error="HIBP returned non-JSON body")

        breaches = self._parse_breaches(payload)
        return self.result(
            "success",
            target,
            data={"email": target, "breaches": breaches, "count": len(breaches)},
        )
