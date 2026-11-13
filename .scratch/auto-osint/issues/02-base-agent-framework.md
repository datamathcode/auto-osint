# 02: Base Agent and Tool Framework

**What to build:** Agent base class with common methods, Tool base class with timeout enforcement and error handling, and a registry pattern for agent and tool discovery. A single SYNINT agent (e.g., WhoisAgent) runs end-to-end as a proof of concept.

**Blocked by:** 01: Setup Project Structure

**Status:** ready-for-agent

- [ ] Agent base class with execute(), observe(), store_evidence(), update_confidence() methods
- [ ] Tool base class with timeout enforcement, rate limiting, error handling
- [ ] Registry pattern: config file that declares available agents and tools
- [ ] Shell wrapper for one SYNINT agent (WhoisAgent) that:
  - Can be invoked independently via CLI
  - Executes the agent and stores evidence to PostgreSQL
  - All base functionality works end-to-end
- [ ] Unit tests for Agent base class
- [ ] Unit tests for Tool base class
- [ ] Integration test for SYNINT agent shell wrapper

**Technical notes:**
- Registry discovery via configuration files (JSON or YAML)
- Timeout enforcement at Tool level (e.g., 60 seconds per tool invocation)
- Rate limiting: max X requests per second per tool
- Error handling: retry with exponential backoff, log errors, return partial results
- Evidence storage: PostgreSQL table `evidence` with columns from design spec
