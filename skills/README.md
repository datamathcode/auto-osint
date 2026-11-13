# Skills for auto-osint

This directory contains reusable skills for auto-osint development.

---

## Engineering Skills

### to-tickets

Break a plan, spec, or conversation into a set of tracer-bullet tickets, each declaring its blocking edges.

**Use when:**
- You have a design or spec that needs to be broken down into actionable work
- You're starting a new feature or large refactor
- You want to create a kanban-ready ticket breakdown

**How to invoke:**
```
skill_view("to-tickets")
```

**Example workflow:**
1. Gather context (read the design document or conversation)
2. Explore the codebase (if needed)
3. Draft vertical slices with blocking edges
4. Quiz the user for approval
5. Publish tickets to tracker or local files

---

## Productivity Skills

### grilling

Grill the user relentlessly about a plan, decision, or idea until every branch of the design tree is resolved.

**Use when:**
- You want to stress-test a design or plan
- The user uses phrases like "is this solid?" or "what am I missing?"
- You need to ensure no assumptions are left silent

**How to invoke:**
```
skill_view("grilling")
```

**How it works:**
- Maps decisions into a design tree
- Works the frontier: questions whose prerequisites are already settled
- Asks the whole frontier in rounds
- Finds facts yourself via subagents; decisions go to the user

**Example:**
```
Round 1:
❓ Q1 - Confidence scoring: Bayesian vs rule-based?
➡️ Bayesian is recommended (more flexible, learnable)
---
❓ Q2 - Independence test: How detailed should it be?
➡️ 3 core questions + 5 supporting checks (detailed but implementable)
```

---

### handoff

Compact the current conversation into a handoff document for another agent to pick up.

**Use when:**
- A new agent needs to continue work from a different session
- You're pausing work and want a clean handoff
- You need to document context, decisions, and next steps

**How to invoke:**
```
skill_view("handoff", "What will the next session be used for?")
```

**What it includes:**
- Summary of current state
- Open questions and decisions made
- Relevant artifacts (design docs, specs)
- Suggested skills for the next agent

---

### writing-for-agents

Writing documents for agents: skills, AGENTS.md/CLAUDE.md, and any doc an agent reaches by a pointer.

**Use when:**
- Creating documentation for other AI agents
- Writing skills, ADRs, or config files
- Creating docs that agents will read as part of their context

**How to invoke:**
```
skill_view("writing-for-agents")
```

**Example artifacts:**
- SKILL.md files
- AGENTS.md
- CLAUDE.md
- Architecture Decision Records (ADRs)
- Specs and designs for agent consumption

---

## Quick Start

1. **Read a skill:**
   ```
   skill_view("to-tickets")
   ```

2. **Use a skill in conversation:**
   ```
   "Use to-tickets to break down the auto-osint design document into tickets"
   ```

3. **Share skills with another agent:**
   ```
   skill_view("handoff", "Start implementing auto-osint following the plan")
   ```

---

## Linking Skills in the Harness

To make these skills available in Claude Code or other agents:

1. Create symlinks to the skills directory:
   ```bash
   # On Linux/macOS
   ln -s /opt/data/sandbox/auto-osint/skills ~/.claude/skills
   ln -s /opt/data/sandbox/auto-osint/skills ~/.agents/skills
   ```

2. Or copy them directly (if symlinks aren't supported):
   ```bash
   cp -r /opt/data/sandbox/auto-osint/skills/* ~/.claude/skills/
   ```

3. Claude Code should automatically discover the skills in `~/.claude/skills`

---

## Source

These skills are from [mattpocock/skills](https://github.com/mattpocock/skills) and have been adapted for the auto-osint project.
