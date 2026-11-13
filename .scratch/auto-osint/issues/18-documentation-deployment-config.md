# 18: Documentation and Deployment Configuration

**What to build:** Complete README with setup instructions, configuration guide, and usage examples. Deployment configuration (Dockerfile, Vercel deployment settings, environment variable documentation). Setup script to initialize PostgreSQL database and create default research playbook. Legal disclaimer and usage guidelines (pre-built safeguards documented).

**Blocked by:** 17: End-to-End Investigation with Synthetic Claim

**Status:** COMPLETE

- [ ] README.md with sections:
  - Project overview (what is auto-osint?)
  - Goals and constraints
  - Prerequisites (Python, Node.js, PostgreSQL, OSINT tools)
  - Quick start guide (5-minute setup)
  - Configuration guide (all environment variables, API keys)
  - Usage examples (step-by-step investigations)
  - Development workflow (running agents, debugging)
  - Troubleshooting common issues
  - Legal disclaimer (ToS compliance, responsible use)
- [ ] Configuration guide:
  - LLM provider setup (Anthropic, OpenAI, Ollama)
  - OpenOSINT tool setup (installing binaries, obtaining API keys)
  - SYNINT setup (installing SYNINT, configuring agents)
  - PostgreSQL setup (creating database, migration scripts)
  - Environment variable reference
- [ ] Deployment configuration:
  - Dockerfile for containerized deployment
  - Vercel deployment settings (build, deploy, environment)
  - CI/CD configuration (GitHub Actions for testing and deployment)
  - Environment variable template (.env.example)
- [ ] Setup script:
  - `scripts/setup.sh` to initialize PostgreSQL schema
  - `scripts/init-playbook.sh` to create default research playbook
  - `scripts/verify-installation.sh` to check prerequisites
- [ ] Legal disclaimer and usage guidelines:
  - Pre-built safeguards documented (scope config, rate limiting, warnings)
  - Responsible use guidelines (only authorized investigations)
  - ToS compliance reminders
  - Chain-of-custody logging explanation
- [ ] License file (MIT, as in mattpocock/skills)
- [ ] Contributing guidelines (if opensourced)

**Technical notes:**
- README should be copy-paste friendly for new users
- Configuration guide should include screenshots or CLI examples
- Setup scripts should be idempotent (can run multiple times safely)
- Deployment configuration should match the tech stack (Next.js + FastAPI + PostgreSQL)
- Legal disclaimer should be prominent in README and UI

**Implementation summary:**
- `README.md` rewritten: overview, goals/constraints, prerequisites table,
  5-minute quick start, configuration pointer, API surface, usage walkthrough
  (create → run → watch → read → learn), development checks, deployment,
  troubleshooting table, and a prominent responsible-use notice.
- `docs/configuration.md` — every environment variable, LLM/OpenOSINT/SYNINT
  setup, limits, frontend behaviour, and deployment notes.
- `docs/legal.md` — intended and prohibited uses, platform-ToS obligations,
  data-minimisation rules, and a table of built-in safeguards mapped to code
  (scope, timeouts, rate limits, concurrency cap, confidence, gaps,
  counter-evidence, chain of custody, key confinement).
- `LICENSE` (MIT, 2026 David Moore) and `CONTRIBUTING.md` (setup, required
  checks, branching, how to add a tool client or playbook section).
- Deployment: `Dockerfile` (API on :8000 with healthcheck and `/data` volume),
  `Dockerfile.web` (Next.js, build-time `NEXT_PUBLIC_API_URL`),
  `docker-compose.yml` (Postgres + API + web, required `POSTGRES_PASSWORD`),
  `vercel.json`, and the existing `.github/workflows/` gates.
- Setup scripts (idempotent, `sh`, honour `PYTHON`/`.venv`/`.env`):
  - `scripts/setup.sh` — initialise the schema.
  - `scripts/init-playbook.sh` — create the playbook only if missing.
  - `scripts/verify-installation.sh` — required checks (Python ≥3.10, package,
    sqlalchemy, fastapi, playbook, schema) plus optional warnings (node,
    sherlock, holehe, SYNINT, `.env`, HIBP key); exits 1 on a hard failure.
- `.env.example` gained `SYNINT_PATH`, `SYNINT_TIMEOUT`, and a playbook override.
- The UI gained a persistent responsible-use footer in `app/layout.tsx`.

**Verification (2026-11-13):**
- `scripts/setup.sh` created all five tables in a fresh SQLite database.
- `scripts/verify-installation.sh` reported every required check `ok` and five
  optional warnings, exiting 0.
- `scripts/init-playbook.sh` is idempotent (reports the existing file, exits 0).
- 222 tests pass, ruff clean, `tsc --noEmit` clean, `next build` OK.

**Not verified here:**
- `docker build` cannot run: the Docker daemon is not available in this
  environment (`Cannot connect to the Docker daemon`). The Dockerfiles and
  compose file are therefore unbuilt, and the Vercel config is not deployed.
