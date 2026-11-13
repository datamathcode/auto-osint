# 08: Integrate OpenOSINT Tools (API Clients)

**What to build:** API clients for 3 OpenOSINT tools (search_username, search_email, search_breach). Each tool has timeout enforcement, rate limiting, and error handling. Tools return structured results with source information. Results are stored in PostgreSQL and can be queried.

**Blocked by:** 07: Integrate SYNINT Agents (Basic Set)

**Status:** COMPLETE

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

**Implementation summary:**
- `src/python/tools/clients/base.py` — `OpenOSINTClient(ToolBase)` with a 60s
  timeout, 10 requests/minute rate limit, `run_binary()` (subprocess with
  timeout and non-zero exit handling), the shared result envelope, and
  `persist()` for `openosint_results`.
- `search_username.py` — sherlock-style client; parses `{site: url}`,
  `{site: {url}}`, `{"sites": …}` and list shapes; non-JSON output yields
  `partial` with the raw text preserved.
- `search_email.py` — holehe-style client; extracts `[+]` hits and URLs from
  text output, rejects malformed addresses.
- `search_breach.py` — HIBP v3 client via `requests`; 404 means "no breaches"
  (success), 401/429/other HTTP errors return explicit failures, key from
  `HIBP_API_KEY` or the constructor.
- `GET /api/results?target_id=&investigation_id=&tool=&limit=` and
  `GET /api/results/{id}` — query stored results by target (investigation
  `target_id` or `target_name`), investigation, or tool.
- All three clients registered in `src/python/tools/config.json`.

**Verification (2026-11-13):**
- `tests/test_openosint_clients.py` (20 tests): parsing shapes, timeout
  enforcement (1s against `sleep 5`), rate limiting (second call blocked),
  missing binary, non-JSON partial results, HIBP 200/404/401/timeout/missing
  key, persistence into `openosint_results`, and the results API by target,
  tool, and id.
- Full suite: 110 passed, ruff clean.
- Note: sherlock/holehe binaries and a live HIBP key are not installed here;
  tests use stub executables and a stubbed HTTP layer.
