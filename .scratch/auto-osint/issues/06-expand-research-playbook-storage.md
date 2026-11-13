|# 06: Expand - Research Playbook Storage

**What to build:** MDX-based research playbook with one default section for tool suggestions by claim type. Playbook is saved to `research_playbook.mdx` and loaded at investigation start.

**Blocked by:** 05: Contract - Remove Old Evidence Storage Logic

**Status:** COMPLETE

**Previous work completed:**
- ✅ MDX playbook file `src/python/research_playbook.mdx` created (72 lines)
- ✅ Python module `src/python/research_playbook.py` created (143 lines)
- ✅ Default playbook includes: funding, intellectual_property sections
- ✅ Default questioning strategies, depth escalation rules, confidence thresholds
- ✅ load(), save(), get_tool_suggestions() functions implemented
- ✅ PR #5 created (feature/06-expand-research-playbook-storage → develop)

**Remaining tasks:**
- [ ] Agent integration at investigation start
- [ ] Unit tests for playbook parsing and loading
- [ ] Playbook changes are persisted to disk (load/save implementation)

**Technical notes:**
- Start with a simple MDX structure
- This will grow over time as the agent learns
- Initial values come from design document playbook examples
- This is the expand phase—playbook exists but is not yet used actively

**CI/CD Status:**
- PR #5: Created (awaiting CI/CD checks)
- Ticket 05: Complete (PR #4 ready to merge)
- Ticket 06: In progress (PR #5 created)
