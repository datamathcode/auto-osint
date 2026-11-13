# 07: Integrate SYNINT Agents (Basic Set)

**What to build:** Shell wrappers for 3 SYNINT agents (WhoisAgent, DNSEnumAgent, MetadataExtractionAgent). Each agent can be invoked independently via CLI with configurable timeouts. Agents store evidence in PostgreSQL with source, timestamp, and raw claim. Evidence can be queried and displayed.

**Blocked by:** 06: Expand - Research Playbook Storage

**Status:** ready-for-agent

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
