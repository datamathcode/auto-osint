# 08: Integrate OpenOSINT Tools (API Clients)

**What to build:** API clients for 3 OpenOSINT tools (search_username, search_email, search_breach). Each tool has timeout enforcement, rate limiting, and error handling. Tools return structured results with source information. Results are stored in PostgreSQL and can be queried.

**Blocked by:** 07: Integrate SYNINT Agents (Basic Set)

**Status:** ready-for-agent

- [ ] API client for search_username (uses sherlock tool or equivalent)
- [ ] API client for search_email (uses holehe tool or equivalent)
- [ ] API client for search_breach (uses HIBP API)
- [ ] Each client:
  - Has timeout enforcement (60s default)
  - Implements rate limiting (e.g., 10 requests/minute)
  - Returns structured results: username/email, platforms found, URLs
  - Logs errors and returns partial results
- [ ] Insert results into PostgreSQL table `openosint_results`
- [ ] API endpoint to query OpenOSINT results by target_id
- [ ] End-to-end test: search for username, query results from DB, display

**Technical notes:**
- OpenOSINT binaries must be installed and accessible in PATH
- API keys stored in environment variables
- Structured output parsing from tool stdout
- Rate limiting per tool to avoid hitting API limits
