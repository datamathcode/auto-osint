"""
OpenOSINT API/tool clients.

Each client wraps one external source, enforces a timeout and rate limit,
returns a structured result dict, and can persist that result to the
``openosint_results`` table through ``save_to_database()``.
"""

from .search_breach import SearchBreachClient
from .search_email import SearchEmailClient
from .search_username import SearchUsernameClient

__all__ = ["SearchUsernameClient", "SearchEmailClient", "SearchBreachClient"]
