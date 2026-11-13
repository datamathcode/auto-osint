# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
