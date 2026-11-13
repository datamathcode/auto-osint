# Ticket completion audit — 2026-11-13

> **Update (same day):** the gaps below were remediated. See
> "Remediation" at the end of this file for commits and re-verification.

Scope: verify that tickets marked COMPLETE actually meet their own acceptance
criteria. Method: read each ticket, then exercise the claimed artifact
(import, run, or test) rather than trusting the checkbox.

## Verdict table

| Ticket | Claimed | Verdict | Why |
|--------|---------|---------|-----|
| 01 Setup project structure | ready-for-agent (all boxes `[x]`) | **NOT DONE** | Backend cannot import; DB setup crashes |
| 02 Base agent/tool framework | COMPLETE | **PARTIAL** | Code and tests real; CLI entry, registry config, end-to-end claim fail |
| 03 Expand confidence module | COMPLETE | **VERIFIED** | Placeholder module matches spec exactly |
| 04 Migrate first evidence batch | COMPLETE | **PARTIAL** | Script and fields real; AgentBase wiring, SQLite→Postgres, integration test absent |
| 05 Contract old evidence storage | COMPLETE | **VERIFIED (trivial)** | No legacy file storage ever existed |
| 06 Expand research playbook | IN_PROGRESS | **VERIFIED, status stale** | Module + tests merged (PR #5); file not updated |

## Evidence

### Ticket 01 — failures

- `src/python/routers/` contains only `__init__.py`. It does
  `from . import dossiers, investigations`, so importing the API fails:

  ```
  $ python -c "from src.python.main import app"
  ImportError: cannot import name 'dossiers' from partially initialized module
  'src.python.routers'
  ```

- `python -m src.python.scripts.setup_database` raises
  `sqlite3.ProgrammingError: You can only execute one statement at a time` —
  the whole schema is passed to one `conn.execute(text(...))`.
- `npm run dev:backend` calls `uv run uvicorn ...`; `uv` is not installed.

Checkboxes that *are* true: Next.js app builds, TypeScript strict,
`.env.example` present, npm scripts present, SQLite schema text present.

### Ticket 02 — what holds and what does not

Holds: `AgentBase` (execute/observe/store_evidence/update_confidence),
`ToolBase` (timeout, retry, rate limit), unit tests for both, SYNINT wrapper
with retry and failure propagation. 59 tests pass.

Does not hold:
- "Can be invoked independently via CLI" — `synint_wrapper.py` has no
  `__main__` block and no argument parsing.
- Registry config is non-functional. `config.json` points at package
  `auto_osint.*`, which does not exist:

  ```
  $ AgentRegistry.register_from_config('src/python/agents/config.json')
  Failed to import agent MockSYNINTAgent: No module named 'auto_osint'
  Failed to import agent SYNINTAgentWrapper: No module named 'auto_osint'
  registered: []
  ```

- "All base functionality works end-to-end" is not demonstrable while the API
  import fails (Ticket 01) and ORM schema creation fails (below).

### Ticket 04 — three overstatements

- "Update AgentBase to use confidence module": no import of
  `confidence_quantization` anywhere under `src/python/agents` or `tools`.
- "Migration script for existing evidence (SQLite to PostgreSQL)": the script
  operates on one session/engine; there is no cross-database transfer.
- "Integration test: full investigation with confidence": no test constructs
  an `Investigation`; `tests/test_migration.py` only mocks a session.

Also: the confidence functions still return placeholder values (0.0 / 0.5),
so a "migrated" entry gets confidence 0.5 from the fallback, not from
quantification.

### Cross-cutting defect found while verifying

Three separate `declarative_base()` instances
(`models/evidence.py`, `models/investigation.py`, `models/openosint_result.py`)
mean ORM table creation fails:

```
$ Evidence.metadata.create_all(engine)
NoReferencedTableError: Foreign key associated with column
'evidence.investigation_id' could not find table 'investigation'
```

`setup_database.py` hides this by creating tables from raw SQL. Any ORM-based
write path breaks until the models share one `Base`.

## What would make 01/02/04 honestly complete

1. Add `routers/investigations.py` and `routers/dossiers.py` (or drop the
   imports), so the FastAPI app imports and `/health` responds.
2. Split the schema into individual statements, or use
   `Base.metadata.create_all` after unifying the declarative base.
3. Fix `agents/config.json` and `tools/config.json` module paths to
   `src.python.agents.*` / `src.python.tools.*`, and add a `__main__` CLI to
   `synint_wrapper.py`.
4. Either wire `AgentBase.store_evidence` to `confidence_quantization` and add
   a real `Investigation` integration test, or retitle Ticket 04's remaining
   checkboxes as future work.

## Remediation (2026-11-13, after the audit)

| Finding | Status | Where |
|---|---|---|
| Backend cannot import (missing routers) | FIXED | `src/python/routers/{investigations,dossiers,evidence}.py`, `main.py` — 9 API tests |
| `setup_database` multi-statement crash | FIXED | `src/python/scripts/setup_database.py` uses `init_db()`; verified with a temp DB |
| Three `declarative_base()` objects | FIXED | `src/python/models/base.py`; `Base.metadata.create_all()` works |
| Registry config points at `auto_osint` | FIXED | `importlib.import_module` + `src.python.*` paths; registry tests |
| No CLI on the SYNINT wrapper | FIXED | `main()` + `scripts/agents/*.sh` + console script; CLI tests |
| AgentBase never used the confidence module | FIXED | `confidence_module` + `set_confidence_module()`; scored in `store_evidence()` |
| No SQLite→PostgreSQL transfer | FIXED | `transfer_evidence()` + `migrate-evidence` CLI |
| No investigation integration test | FIXED | `tests/test_integration_investigation.py` |
| Ticket 06 status stale | FIXED | ticket file set to COMPLETE |

Ticket statuses now: 01–07 COMPLETE, 08–18 ready-for-agent.

Re-verification at release: **90 tests pass**, ruff clean, CI green on
Python 3.10 and 3.11. Released through PR #6 (tickets 01–06) and PR #8
(ticket 07).

Remaining known limitation: evidence storage is PostgreSQL-capable through
`DATABASE_URL`, but no PostgreSQL server is configured in this environment, so
all runs and tests use SQLite.
