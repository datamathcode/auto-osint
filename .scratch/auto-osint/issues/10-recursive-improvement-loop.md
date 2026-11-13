# 10: Recursive Improvement Loop

**What to build:** Post-investigation analysis framework that runs after completion, identifies gaps and successful patterns, updates research playbook, and loads updated playbook for next investigation.

**Blocked by:** 09: Base LLM Orchestration Layer

**Status:** ready-for-agent

- [ ] Post-investigation analysis function:
  - Reads investigation results from PostgreSQL
  - Identifies gaps: sources not queried, questions not answered
  - Identifies successful patterns: tool ordering, questioning strategies
- [ ] Playbook update logic:
  - Creates new section in playbook: "lessons_learned_<timestamp>"
  - Documents gaps and successful patterns
  - Saves updated playbook to disk
- [ ] Playbook retrieval in next investigation:
  - Loads most recent playbook version
  - Uses as starting point for tool selection
  - Adapts based on real-time findings
- [ ] Unit tests for analysis and update logic
- [ ] Integration test: run investigation, analyze results, update playbook, run second investigation

**Technical notes:**
- Playbook is MDX format for easy editing and versioning
- Store playbook update references in `investigation_summary` table
- Learning should be incremental—don't rewrite entire playbook on each run
- Gap identification should use heuristics (e.g., unanswered questions, missing source types)
