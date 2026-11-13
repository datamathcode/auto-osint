# 10: Recursive Improvement Loop

**What to build:** Post-investigation analysis framework that runs after completion, identifies gaps and successful patterns, updates research playbook, and loads updated playbook for next investigation.

**Blocked by:** 09: Base LLM Orchestration Layer

**Status:** COMPLETE

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

**Implementation summary:**
- `src/python/learning.py`
  - `analyze_investigation(session, id)` — reads evidence and
    `openosint_results`; gaps come from failed tool results, missing evidence,
    or missing results; patterns come from productive sources and the order of
    tools that succeeded.
  - `update_playbook(analysis, path, label)` — appends one
    `lessons_learned_<timestamp>` record to the existing front matter, preserving
    the body and all other sections, keeping the newest 10 lessons.
  - `record_on_investigation()` — writes the lesson label to
    `Investigation.playbook_update` (the repo has no `investigation_summary`
    table; this column is the equivalent reference).
  - `recommended_tools(metadata, claim_type)` — tools that previously succeeded
    for this claim type, most recent first.
- `Orchestrator.plan_investigation()` now loads the current playbook and
  reorders steps so learned tools run first.
- `Orchestrator.observe_tool_output()` persists each tool result through
  `ToolBase.persist()` and attaches the session to every tool, so analyses see
  what actually ran.

**Verification (2026-11-13):**
- `tests/test_learning.py` (8 tests): analysis of gaps/patterns from real rows,
  empty-investigation gaps, unknown investigation, lesson append preserving the
  Markdown body, retention cap at 10, existing sections preserved, learned tool
  ordering, and the full loop (run → analyse → update → second run plans the
  learned tool first).
- Full suite: 138 passed, ruff clean.
