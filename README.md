# auto-osint

Agentic recursive OSINT research with data journalism rigor.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-222%20passing-brightgreen)](tests/)
[![Release](https://img.shields.io/badge/release-v0.1.0-blue)](https://github.com/datamathcode/auto-osint/releases)

> **Responsible use.** This tool automates open-source collection. You are
> responsible for complying with platform terms of service and the law. Read
> [docs/legal.md](docs/legal.md) before your first investigation. Do not use it
> to profile private individuals, minors, or anyone you are not entitled to
> investigate.

## What it is

auto-osint plans an investigation from a claim, chooses tools from a research
playbook, runs them in parallel, stores every finding with its source and a
confidence score, and produces a dossier showing supporting evidence,
counter-evidence, gaps, a timeline, and an entity network.

The loop is deliberately transparent: it does not invent confidence, and every
section traces back to a stored row.

## Goals and constraints

- **Verifiable output** — every claim links to sources, raw output, and a chain
  of custody.
- **Honest weakness** — low confidence, missing source types, unanswered
  questions, and source bias are reported rather than smoothed over.
- **Bounded collection** — scope, timeouts, rate limits, and a concurrency cap.
- **Provider-agnostic reasoning** — the orchestration loop runs without an LLM;
  `reasoning_hook` is where a model attaches.

## Prerequisites

| Need | Version | Why |
|---|---|---|
| Python | 3.10+ | API, agents, orchestrator |
| Node.js | 18+ | Next.js frontend |
| SQLite | bundled | Default local database |
| PostgreSQL | 14+ | Production database (optional) |
| `sherlock`, `holehe` | latest | Username / email clients (optional) |
| SYNINT | your build | Shell agents (optional) |

Missing optional tools are reported as gaps, not crashes.

## Quick start (5 minutes)

```bash
git clone https://github.com/datamathcode/auto-osint.git
cd auto-osint

# backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # defaults point at SQLite; leave keys blank
python -m src.python.scripts.setup_database

# frontend
npm install

# run both
python -m src.python.main          # API on :8000
npm run dev:frontend               # UI on :3000
```

Open <http://localhost:3000/investigate>, enter a target and a claim, then press
**Start investigation**. With no external tools installed the run still
completes and the dossier reports the missing sources as gaps.

### Verify the install

```bash
./scripts/verify-installation.sh
```

### Run one agent from the CLI

```bash
synint-wrapper --synint-path ./path/to/synint --agent WhoisAgent \
  --target example.com --investigation-id 1
```

## Configuration

Full reference: [docs/configuration.md](docs/configuration.md).

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/auto_osint
LLM_PROVIDER=anthropic          # anthropic | openai | ollama
ANTHROPIC_API_KEY=...           # optional; never returned by the API
HIBP_API_KEY=...                # required for breach lookups
SYNINT_PATH=/usr/local/bin/synint
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Never commit `.env`. The API exposes only key *presence* at
`GET /api/config/defaults`, never values.

## Usage walkthrough

1. **Create** — `/investigate`, or `POST /api/investigations` with
   `target_name`, `claim_under_investigation`, and optional `scope`
   (dates, platforms, data types, 5–60 minute budget).
2. **Run** — `POST /api/orchestrate/async` returns `202` with stream URLs.
   Events: `investigation_started`, `plan_generated`, `step_started`, `finding`,
   `step_finished`, `confidence_updated`, `refinement`, `investigation_complete`.
3. **Watch** — `/investigations/{id}/progress` (WebSocket, auto-reconnect) or
   `GET /sse/investigation/{id}`.
4. **Read** — `/dossiers/{id}`: verdict, confidence counters, paginated evidence,
   counter-evidence, timeline, entity network, gaps, improvement log.
5. **Learn** — each completed run appends a `lessons_learned_*` record to the
   playbook, which reorders tools on the next investigation.

### API surface

| Method | Path | Purpose |
|---|---|---|
| POST/GET | `/api/investigations` | create / list |
| GET/PATCH | `/api/investigations/{id}` | read / update |
| GET | `/api/investigations/{id}/evidence` | evidence for one run |
| POST | `/api/orchestrate` | run synchronously |
| POST | `/api/orchestrate/async` | run in background (`resume` supported) |
| GET | `/api/dossiers/{id}` … `/timeline` `/graph` `/gaps` `/playbook-update` | dossier sections |
| GET | `/api/evidence`, `/api/results` | query by target or tool |
| GET | `/api/timeline/{id}`, `/api/graph/{id}`, `/api/audit/{id}` | visualisation data |
| GET | `/api/config/defaults` | non-secret defaults |
| GET/WS | `/sse/investigation/{id}`, `/ws/investigation/{id}` | progress |

## Development workflow

```bash
ruff check src/python/ tests/          # lint
python -m pytest tests/ -q             # 222 tests
npx tsc --noEmit                       # type check
npx next build                         # production build
```

Branches: `feature/<ticket>-<slug>` → `develop` → `main`. See
[BRANCHING.md](BRANCHING.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## Deployment

```bash
docker compose up --build       # Postgres + API + web
```

- `Dockerfile` — API image (`python -m src.python.main`).
- `Dockerfile.web` — Next.js image.
- `vercel.json` — frontend deployment settings.
- `.github/workflows/` — tests, lint, build, security scan, deploy gates.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `No module named 'src'` | run from a subdirectory | run from the repo root, or `pip install -e .` |
| `No module named 'httpx'` | dev extras missing | `pip install -e ".[dev]"` |
| `You can only execute one statement at a time` | stale setup script | use `python -m src.python.scripts.setup_database` |
| Dossier shows "Could not load" | API down or wrong URL | check `NEXT_PUBLIC_API_URL` and `/health` |
| `HIBP_API_KEY is not set` | breach lookups disabled | add the key, or accept the gap report |
| `sherlock is not installed` | binary missing | `pip install sherlock-project`, or pass `binary=` to the client |
| Progress page stuck on "connecting" | WebSocket blocked by a proxy | use the SSE endpoint instead |
| Tests pass locally, red in CI | interpreter drift | CI covers 3.10 and 3.11 |

## Legal disclaimer

Open-source intelligence collection is regulated. Use this software only for
lawful investigations you are authorised to conduct, respect each platform's
terms of service, and comply with privacy law. The [full disclaimer](docs/legal.md)
lists the built-in safeguards (scope bounds, timeouts, rate limits, confidence
scoring, gap detection, chain of custody) and the uses this project is not
intended for.

## Documentation

- [Configuration reference](docs/configuration.md)
- [Legal and responsible use](docs/legal.md)
- [Design document](docs/superpowers/specs/2026-11-12-auto-osint-design.md)
- [Contributing](CONTRIBUTING.md) · [Branching](BRANCHING.md)

## Licence

MIT — see [LICENSE](LICENSE).
