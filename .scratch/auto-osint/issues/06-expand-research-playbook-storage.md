# 06: Expand - Research Playbook Storage

**What to build:** MDX-based research playbook with one default section for tool suggestions by claim type. Playbook is saved to `research_playbook.mdx` and loaded at investigation start.

**Blocked by:** 05: Contract - Remove Old Evidence Storage Logic

**Status:** ready-for-agent

- [ ] MDX playbook file `src/python/research_playbook.mdx` with:
  - version field
  - last_updated field
  - one section: "funding" with suggested_tools: ["SEC filings", "corporate registries"]
  - default questioning strategies
  - default depth_escalation_rules
  - default confidence_thresholds
- [ ] Python module `src/python/research_playbook.py` with load() and save() functions
- [ ] Agent can read and parse the playbook at investigation start
- [ ] Playbook changes are persisted to disk
- [ ] Unit tests for playbook parsing and loading

**Technical notes:**
- Start with a simple MDX structure
- This will grow over time as the agent learns
- Initial values come from design document playbook examples
- This is the expand phase—playbook exists but is not yet used actively
