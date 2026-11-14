# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Cloudflare Workers deployment for the frontend. The Next.js app is adapted with
  `@opennextjs/cloudflare@1.15.0` — the last release that supports Next 14 — and
  ships `wrangler.jsonc`, `open-next.config.ts`, and `npm run preview|deploy`.
- `/api/proxy/[...path]` forwards browser requests to the API and attaches the
  Cloudflare Access service token server-side, so the credential stays on the
  Worker. Server components call the API directly with the same headers.

### Changed

- The root page lists the six most recent investigations instead of showing a
  hardcoded "Setup in progress..." placeholder. It is server-rendered, so it
  reads the API on each request and says so plainly when the API is unreachable.
- The progress page streams with SSE instead of WebSocket. A Worker cannot
  upgrade a socket without a Durable Object, and the backend already exposes
  `/sse/investigation/{id}`.

### Fixed

- Docker Compose stack. Added a `.dockerignore`, so `Dockerfile.web`'s
  `COPY . .` no longer copies the host's `node_modules` and `.next` over the
  dependencies installed in the image — that broke native modules when the host
  was macOS and the image Linux, and it inflated the build context. The `web`
  service now waits for a healthy `api`; all three services restart unless
  stopped; and the API receives `OLLAMA_BASE_URL`, `OLLAMA_MODEL`,
  `MAX_EXECUTION_TIME` and `TIMEOUT_PER_TOOL`, which the application reads.
- The README's deployment section documents the required `POSTGRES_PASSWORD`,
  the services and ports, build-time `NEXT_PUBLIC_API_URL`, teardown, and the
  standalone API image that falls back to SQLite on `/data`.
- Tool clients now run the binaries they name. `build_tools()` passed no
  `binary`, so every client defaulted to its tool name (`search_username`) and
  failed with "not installed" even when sherlock was on `PATH`. The clients now
  use `sherlock` and `holehe`, overridable with `SHERLOCK_BIN` and `HOLEHE_BIN`.
- `TIMEOUT_PER_TOOL` is applied to each client. It was documented and reported
  by `/api/config/defaults`, but never reached a client, so every call used the
  hard-coded 60 s default.
- Username lookups use flags sherlock accepts. The client passed `--json`, which
  in sherlock means "load site definitions from a file", so the binary exited 2
  with a usage error. It now runs `--print-found --no-color --timeout <n>` and
  parses `[+] Platform: URL` lines, keeping JSON parsing as a fallback for other
  CLIs.
- A full sherlock scan no longer exceeds the tool timeout. Sherlock waits 60 s
  per site by default; across roughly 400 sites that is minutes. The request
  timeout is now 10 s (`SHERLOCK_TIMEOUT`), which takes a full scan from over
  three minutes to about twenty seconds.

## [0.2.1] - 2026-11-13

### Added

- Architecture diagram at `docs/images/architecture.svg`, showing the pipeline from
  the investigate form through orchestration, collection, evidence storage, the
  dossier, and the playbook feedback loop.

### Changed

- Rewrote `README.md` for a first-time reader: overview, five-step quick start,
  how the pipeline works, an honest project-status table, API surface,
  configuration, development checks, deployment, and troubleshooting.
- Corrected claims in the README that overstated the code: confidence scoring is
  a fixed `0.6` / `0.3` heuristic, not a Bayesian posterior, and `resume` applies
  to the synchronous orchestration endpoint only.

### Fixed

- The frontend rendered without any CSS. The repository had no `postcss.config.js`,
  so Tailwind directives were served unprocessed. Added the config; utility classes
  now compile.
- `.env.example` defaulted `DATABASE_URL` to PostgreSQL with a committed password,
  which broke the documented first run. It now defaults to SQLite, keeps the
  PostgreSQL example commented, and documents `POSTGRES_PASSWORD`.
- `scripts/verify-installation.sh` redirected the output of its database-schema
  check to `/dev/null`, hiding both success and failure. The check now reports.
- CI: the required checks (lint, security scan, dependency scan) and the test
  workflow now run on pull requests to `main`. The `main` ruleset requires them,
  but the workflows previously triggered only for `develop`, so release pull
  requests could never satisfy the gate.

## [0.2.0] - 2026-11-13

### Added

- Documentation: `README`, `docs/configuration.md` (every environment variable),
  and `docs/legal.md` (intended and prohibited uses, platform obligations, and a
  safeguards table mapped to the code).
- Project files: `LICENSE` (MIT), `CONTRIBUTING.md`, and `BRANCHING.md` for the
  `feature → develop → main` flow.
- Deployment: `Dockerfile` (API, healthcheck, `/data` volume), `Dockerfile.web`,
  `docker-compose.yml` (PostgreSQL, API, web), and `vercel.json`.
- Idempotent scripts: `scripts/setup.sh`, `scripts/init-playbook.sh`, and
  `scripts/verify-installation.sh`.
- Responsible-use notice in the application footer.

### Changed

- Version set to `0.2.0` in `package.json` and `pyproject.toml`.
- `.env.example` documents the full runtime configuration.

## [0.1.0] - 2026-11-13

### Added

- Investigation API and `/investigate` form: target, claim, date range, platforms,
  data types, and a 5–60 minute budget.
- Deterministic **plan → execute → observe → refine** orchestrator, with an optional
  LLM through `reasoning_hook`, playbook-driven tool selection, a concurrency cap,
  per-tool timeouts, rate limits, retries, and resume support.
- OpenOSINT clients for usernames (sherlock), email (holehe), and breaches (HIBP),
  plus a SYNINT wrapper CLI and `whois`, `dns-enum`, and `metadata-extraction` agents.
- Evidence store with source, confidence, independence score, contradictions, links,
  raw output, and an append-only chain of custody. SQLite by default; PostgreSQL
  through `DATABASE_URL`.
- Self-audit: missing source types, unanswered questions, unqueried tools, weight
  and source-bias analysis.
- Dossier: verdict, confidence counters, paginated evidence, counter-evidence, D3
  timeline, React Flow entity network, gaps, improvement log, and print-to-PDF.
- Progress over Server-Sent Events and WebSocket, with heartbeat and event replay.
- Learning loop: completed runs append `lessons_learned_*` records to the research
  playbook, which reorder tools on the next run.

[0.2.1]: https://github.com/datamathcode/auto-osint/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/datamathcode/auto-osint/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/datamathcode/auto-osint/releases/tag/v0.1.0
