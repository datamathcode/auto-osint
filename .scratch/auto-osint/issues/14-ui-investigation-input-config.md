# 14: UI - Investigation Input and Configuration

**What to build:** Next.js page for inputting investigation parameters: target name, claim, scope (time ranges, platforms, data types). Configuration form for API keys (LLM provider, OSINT tool APIs). Default configurations loaded from environment variables or local config file. User can start a new investigation from this page.

**Blocked by:** 07: Integrate SYNINT Agents (Basic Set), 08: Integrate OpenOSINT Tools (API Clients)

**Status:** ready-for-agent

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
