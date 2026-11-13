# Configuration reference

Every value is read from the environment (a local `.env` is loaded by the API
and by the scripts). Nothing below is required for tests — they run against
temporary SQLite databases.

## Database

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/auto_osint.db` | Use `postgresql://user:pass@host:5432/db` for PostgreSQL |

`python -m src.python.scripts.setup_database` (or `auto-osint-db`) creates every
table from the shared SQLAlchemy metadata and is safe to re-run.

## LLM provider

The orchestration loop is deterministic by default. `reasoning_hook` in
`src/python/orchestrator.py` is where a provider is attached.

| Variable | Default | Notes |
|---|---|---|
| `LLM_PROVIDER` | `anthropic` | `anthropic`, `openai`, or `ollama`; surfaced by `GET /api/config/defaults` |
| `ANTHROPIC_API_KEY` | unset | Presence is reported, value never returned |
| `OPENAI_API_KEY` | unset | Same |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local models |
| `OLLAMA_MODEL` | empty | Model tag for local runs |

## OpenOSINT tools

| Variable | Notes |
|---|---|
| `HIBP_API_KEY` | Required for `search_breach`; without it the client returns a failure that appears as a gap |
| `HOLEHE_API_KEY` | Reserved for hosted email lookups |

Binaries must be on `PATH` (or passed explicitly):

```bash
pip install sherlock-project   # search_username
pip install holehe             # search_email
which sherlock holehe
```

## SYNINT

| Variable | Default | Notes |
|---|---|---|
| `SYNINT_PATH` | `synint` | Used by `scripts/agents/*.sh` |
| `SYNINT_TIMEOUT` | `300` | Per-run seconds |

## Limits and application

| Variable | Default | Notes |
|---|---|---|
| `MAX_EXECUTION_TIME` | `3600` | Seconds; also reported to the UI |
| `TIMEOUT_PER_TOOL` | `60` | Per tool invocation |
| `MAX_CONCURRENT_QUERIES` | `8` | Orchestrator parallel tool calls |
| `API_HOST` / `API_PORT` | `0.0.0.0` / `8000` | API bind address |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Frontend → API base URL |

## Frontend

The `/investigate` page reads `GET /api/config/defaults` for non-secret defaults
and stores user configuration (including API keys typed into the form) in
`localStorage` under `auto-osint-config`. Keys typed there stay in the browser;
they are not sent to the API.

## Deployment

- **API**: `Dockerfile`, listens on `8000`, reads the variables above.
- **Frontend**: `Dockerfile.web`, needs `NEXT_PUBLIC_API_URL` at build time.
- **Vercel**: `vercel.json` builds the Next.js app from the repo root.
- **Compose**: `docker-compose.yml` brings up Postgres + API + web.

Secrets belong in the platform's secret store, never in the image or the repo.
