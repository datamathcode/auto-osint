# 07: Integrate SYNINT Agents (Basic Set)

**What to build:** Shell wrappers for 3 SYNINT agents (WhoisAgent, DNSEnumAgent, MetadataExtractionAgent). Each agent can be invoked independently via CLI with configurable timeouts. Agents store evidence in PostgreSQL with source, timestamp, and raw claim. Evidence can be queried and displayed.

**Blocked by:** 06: Expand - Research Playbook Storage

**Status:** COMPLETE

- [ ] Shell wrapper scripts for WhoisAgent, DNSEnumAgent, MetadataExtractionAgent
- [ ] Each wrapper:
  - Accepts command-line arguments (target URL/hostname, timeout)
  - Executes corresponding SYNINT agent binary
  - Captures output and extracts evidence
  - Inserts evidence into PostgreSQL `evidence` table
  - Returns exit code and summary
- [ ] PostgreSQL table `evidence` with schema from design spec
- [ ] Evidence entries include: source, timestamp, claim, raw text
- [ ] API endpoint to query evidence by target_id
- [ ] CLI command to invoke a single SYNINT agent
- [ ] End-to-end test: invoke WhoisAgent, query evidence from DB, display

**Technical notes:**
- SYNINT binaries must be installed and accessible in PATH
- Use subprocess with timeout enforcement
- Parse SYNINT output to extract structured evidence
- Store raw text for debugging and later analysis

**Implementation summary:**
- `scripts/agents/whois-agent.sh`, `dns-enum-agent.sh`,
  `metadata-extraction-agent.sh` — thin POSIX wrappers around
  `python -m src.python.agents.synint_wrapper`, honouring `SYNINT_PATH` and
  `SYNINT_TIMEOUT`; exit 2 with usage when the target is missing.
- Console entry points in `pyproject.toml`: `synint-wrapper`, `auto-osint-db`,
  `migrate-evidence`.
- `Evidence.raw_text` column stores unparsed agent output; `store_evidence()`
  accepts `raw_text`, and the wrapper fills it with subprocess stdout.
- Wrapper returns a `summary` block (claim, confidence, evidence_id, exit_code)
  and exits 0/1 for scripting.
- `GET /api/evidence?target_id=…&investigation_id=…&source=…` queries evidence by
  target (matching `Investigation.target_id` or `target_name`);
  `GET /api/evidence/{id}` returns the full row including chain of custody.
- Database is PostgreSQL-compatible through `DATABASE_URL`; tests and local runs
  use SQLite files because no PostgreSQL server is configured here.

**Verification (2026-11-13):**
- `tests/test_ticket07_synint_integration.py` runs each of the three agents
  through the CLI into a real SQLite file, asserts three evidence rows with
  distinct sources and non-empty `raw_text`, then queries them over HTTP by
  `target_id`, by `source`, and by evidence id (including chain of custody).
- Shell wrappers are executed with a recording `python` shim to prove each one
  forwards `--agent`, `--target`, `--timeout`, and `--synint-path`.
- Full suite: 82 passed, ruff clean.
