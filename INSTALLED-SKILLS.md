# Installed Skills Summary

**Date:** 2026-11-12  
**From:** mattpocock/skills repository  
**Location:** `/opt/data/sandbox/auto-osint/skills/`

---

## Skills Installed

### Engineering Skills

1. **to-tickets** (`skills/engineering/to-tickets/SKILL.md`)
   - Purpose: Break plans, specs, and conversations into actionable tracer-bullet tickets
   - Blocking edges: Each ticket declares which tickets must complete before it can start
   - Vertical slicing: Each slice is complete and demoable on its own
   - Local or tracker publishing with dependency tracking

2. **grilling** (`skills/productivity/grilling/SKILL.md`)
   - Purpose: Relentlessly interview the user about a plan, decision, or idea
   - Design tree: Maps decisions into branches with unresolved questions
   - Frontier approach: Asks all questions whose prerequisites are settled
   - Rounds: Organized by unresolved prerequisites

### Productivity Skills

3. **handoff** (`skills/productivity/handoff/SKILL.md`)
   - Purpose: Compact conversation context into handoff documents for other agents
   - Output: Temporary directory ($TMPDIR or /tmp)
   - Includes: Summary, open questions, decisions, relevant artifacts, suggested skills
   - Redaction: Strips sensitive information (API keys, passwords, PII)

4. **writing-for-agents** (`skills/productivity/writing-for-agents/SKILL.md`)
   - Purpose: Write documents that other AI agents will read
   - Includes: SKILL.md files, AGENTS.md, CLAUDE.md, ADRs, specs
   - Target audience: Agents, not humans
   - Format: Dense, structured, pointer-referenced

---

## What These Skills Enable

**to-tickets + grilling together:**
- Take the auto-osint design document
- Use grilling to validate all design decisions
- Use to-tickets to break the design into actionable tickets with blocking edges
- Publish tickets to tracker or local files
- Create a clear implementation roadmap

**handoff:**
- Pause work and hand off to another agent with full context
- Document decisions, open questions, and next steps
- Suggest relevant skills for the next agent

**writing-for-agents:**
- Write skills, ADRs, and documentation that agents will use as context
- Structure information in a way agents can reason about
- Use pointer references instead of duplicating content

---

## Usage Examples

### Break Down Design into Tickets

```
"Use grilling to stress-test the auto-osint design decisions about confidence quantification"

"Use to-tickets to break the auto-osint design into actionable tickets with blocking edges"
```

### Hand Off Work

```
"Use handoff to prepare for a new agent continuing the auto-osint implementation"
```

### Write Agent-Readable Docs

```
"Use writing-for-agents to write a skill for Bayesian confidence calculation"
```

---

## Next Steps

1. ✅ Skills installed
2. ⏭️ Use grilling to validate design decisions (optional but recommended)
3. ⏭️ Use to-tickets to break design into implementation roadmap
4. ⏭️ Start implementing tickets

---

**Skills directory:** `/opt/data/sandbox/auto-osint/skills/`  
**Skill README:** `/opt/data/sandbox/auto-osint/skills/README.md`
