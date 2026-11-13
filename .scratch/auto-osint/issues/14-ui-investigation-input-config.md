# 14: UI - Investigation Input and Configuration

**What to build:** Next.js page for inputting investigation parameters: target name, claim, scope (time ranges, platforms, data types). Configuration form for API keys (LLM provider, OSINT tool APIs). Default configurations loaded from environment variables or local config file. User can start a new investigation from this page.

**Blocked by:** 07: Integrate SYNINT Agents (Basic Set), 08: Integrate OpenOSINT Tools (API Clients)

**Status:** COMPLETE

- [ ] Next.js page `/investigate` for investigation input
- [ ] Form fields:
  - Target name (text input)
  - Claim to investigate (textarea)
  - Investigation scope:
    - Time range (start date, end date)
    - Platforms to query (checkboxes: Twitter/X, LinkedIn, GitHub, etc.)
    - Data types (checkboxes: filings, news, academic, etc.)
  - Max execution time (slider: 5–60 minutes)
- [ ] Configuration form for API keys:
  - LLM provider (select: Anthropic, OpenAI, Ollama)
  - LLM API key (password field, masked)
  - OpenOSINT API keys (search_username, search_email, search_breach)
  - SYNINT tool paths (if not in PATH)
  - PostgreSQL connection string
- [ ] Default configurations:
  - Loaded from environment variables (`.env`)
  - Fall back to local config file if env vars not set
  - Config values saved to browser localStorage
- [ ] Start investigation button triggers backend investigation
- [ ] Error handling for missing API keys
- [ ] Validation for required fields

**Technical notes:**
- Form uses React Hook Form for validation
- API key storage is client-side only (browser localStorage)
- PostgreSQL connection is server-side, not client
- Scope options based on design document supported source types

**Implementation summary:**
- `app/investigate/page.tsx` (React Hook Form, client component):
  - target name, claim textarea, start/end dates (validated: end >= start),
    platform checkboxes (twitter/linkedin/github/reddit/instagram/facebook),
    data-type checkboxes (filings/news/academic/registries/breach/social), and a
    5–60 minute execution-time slider.
  - Configuration panel: LLM provider select, masked LLM key, masked HIBP key,
    SYNINT binary path, and a read-only server-side database URL.
  - Defaults come from `GET /api/config/defaults` (env-derived, secrets reduced
    to booleans); user config is persisted to `localStorage` under
    `auto-osint-config` and restored on load.
  - Start button creates the investigation, optionally runs
    `POST /api/orchestrate`, then navigates to `/dossiers/{id}`; API and network
    errors are shown inline, and a missing `HIBP_API_KEY` is surfaced as a warning.
- `src/python/routers/config.py`: `GET /api/config/defaults` (llm provider list,
  key presence flags, SYNINT path, database URL, limits; never secret values).
- `Investigation.scope` JSON column; create accepts and validates scope
  (date ordering, 5–60 minute budget) and returns it.

**Verification (2026-11-13):**
- `tests/test_config_and_scope.py` (9 tests): defaults shape, secrets never
  returned, missing/present key flags, provider from env, scope persistence and
  echo, optional scope, reversed dates, execution-time bounds, required fields.
- `npx tsc --noEmit` clean; `next build` emits `/investigate` (15.1 kB).
- Full suite: 197 passed, ruff clean.
- Deviation: no frontend unit-test runner exists in this repo, so the page is
  verified by type-checking and production build rather than component tests.
