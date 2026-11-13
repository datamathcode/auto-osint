# AGENTS.md

**File:** AGENTS.md  
**Purpose:** Rules for how AI agents should interact with this codebase.

---

## Overview

This file documents the conventions and rules that AI agents (including future subagents) should follow when working with auto-osint. It covers:

- Reading and writing files
- Using the Skill tool
- Codebase navigation
- Testing and validation
- Documentation standards

---

## File Operations

### Reading Files

When reading files:

1. **Read the full file if under 100KB:** No pagination needed
2. **For large files (>100KB):**
   - Start with the first 500 lines to understand structure
   - If you need specific sections, use `search_files` or `read_file` with `limit` parameter
3. **Markdown files:** Read entire file; use `search_files` for targeted content
4. **Code files:** Read entire file to understand context; use grep for specific patterns

**Example:**
```typescript
// Correct
const content = read_file(path="src/python/agent.py")

// For large files (optional)
const firstLines = read_file(path="src/python/agent.py", limit=100)
const middleLines = read_file(path="src/python/agent.py", offset=500, limit=100)
```

### Writing Files

When writing files:

1. **Use `write_file` for new files:** It creates parent directories automatically
2. **Confirm write success:** Check the `verified` field in the result
3. **Never overwrite user content without reading first:** If a file exists, read it before writing
4. **For patches:** Use `patch` instead of `write_file` when modifying existing files

**Example:**
```typescript
// Correct - create new file
write_file(
  path="src/python/agent.py",
  content="import os\nprint('Hello')"
)

// Correct - verify write
const result = write_file(path="src/python/agent.py", content="...")
if (result.verified) {
  console.log("File written successfully")
}
```

---

## Skill Tool Usage

### Invoking Skills

When invoking skills:

1. **Always use `skill_view` to load a skill first:**
   ```typescript
   skill_view("to-tickets")
   ```

2. **Skills are in `skills/` directory:** All skills are stored under `skills/` in the repo root
3. **Use qualified names for superpowers skills:**
   ```typescript
   skill_view("superpowers:to-tickets")
   skill_view("superpowers:grilling")
   ```

4. **Never invent skill names:** All skills must exist in `skills/` or be from the mattpocock/skills plugin

### Skill-First Workflow

When starting a new task:

1. **Check if a skill exists:**
   ```typescript
   skill_view("skill-name")
   ```

2. **If the skill doesn't exist in local `skills/`, check mattpocock/skills:**
   ```typescript
   skill_view("mattpocock-skill-name")  // from the plugin
   ```

3. **Follow the skill's instructions precisely:** Skills are designed to guide you correctly

4. **Report when you've completed a skill:**
   ```
   "Using to-tickets skill to break down the design..."
   ```

---

## Codebase Navigation

### Directory Structure

Key directories:

```
auto-osint/
├── app/              # Next.js app directory (frontend)
├── src/              # Source code (backend)
│   ├── python/       # Python backend
│   │   ├── agents/   # Agent implementations
│   │   ├── tools/    # Tool implementations
│   │   └── playbooks/# Research playbooks
│   └── types/        # TypeScript types
├── skills/           # Skills for AI agents
├── docs/             # Documentation
└── .scratch/         # Scratch files, tickets
```

### Finding Information

1. **To find a specific file:**
   ```typescript
   search_files(pattern="filename", target="files", path="src/python")
   ```

2. **To find a skill:**
   ```typescript
   search_files(pattern="SKILL.md", target="files", path="skills")
   ```

3. **To find documentation:**
   ```typescript
   search_files(pattern="README.md", target="files", path=".")
   ```

### Understanding the Codebase

1. **Start with README.md:** Understand the project overview and goals
2. **Read the design document:** `/docs/superpowers/specs/2026-11-12-auto-osint-design.md`
3. **Check ticket files:** `/scratch/auto-osint/issues/01-*.md` for current work
4. **Review skills:** Check `skills/` for available skills and their purposes

---

## Testing and Validation

### Running Tests

1. **For Python backend:**
   ```bash
   uv run pytest
   # or
   uv run python -m pytest
   ```

2. **For frontend:**
   ```bash
   npm run test
   # or
   uv run npm test
   ```

3. **For linting:**
   ```bash
   npm run lint
   # or
   uv run npm run lint
   ```

### Validation Checklist

Before marking a ticket complete:

1. **Read the ticket:** Confirm all acceptance criteria are met
2. **Run tests:** Tests must pass
3. **Verify documentation:** README, tickets, and AGENTS.md are up to date
4. **Test manually:** If applicable, test the feature manually
5. **Check git status:** No uncommitted changes except scratch files

---

## Documentation Standards

### Markdown Files

When creating or updating documentation:

1. **Use consistent headings:** H1 (#) for page titles, H2 (##) for sections, H3 (###) for subsections
2. **Include a TL;DR:** One-sentence summary at the top
3. **Link to related files:** Use relative paths (e.g., `docs/setup.md`, `skills/to-tickets/SKILL.md`)
4. **Use code blocks:** Wrap code in triple backticks with language identifier
5. **Add examples:** Show concrete examples whenever possible

### Ticket Files

When creating tickets (in `.scratch/auto-osint/issues/`):

1. **Name files with leading zero:** `01-ticket-name.md`, `02-ticket-name.md`
2. **Use clear, descriptive titles:** Ticket titles should be self-explanatory
3. **Include blocked-by field:** List all tickets that must complete first
4. **Provide acceptance criteria:** Clear, testable criteria
5. **Add technical notes:** Implementation details and tradeoffs

### Code Comments

When adding code comments:

1. **Use JSDoc/PythonDoc style:** Clear, descriptive comments
2. **Explain the "why", not the "what":**
   ```python
   # CORRECT
   # Calculate Bayesian posterior: P(H|E) = P(E|H) * P(H) / P(E)
   posterior = (likelihood * prior) / evidence

   # INCORRECT
   # Divide likelihood by evidence
   posterior = likelihood / evidence
   ```

3. **Comment complex logic:** Explain non-obvious algorithms or business rules

---

## Git Conventions

### Commit Messages

When committing:

1. **Follow conventional commits format:**
   ```
   <type>(<scope>): <subject>
   ```

2. **Common types:**
   - `feat`: New feature
   - `fix`: Bug fix
   - `docs`: Documentation changes
   - `style`: Code style changes (formatting, no logic change)
   - `refactor`: Code refactoring
   - `test`: Test additions or changes
   - `chore`: Build process or auxiliary tool changes

3. **Examples:**
   ```
   feat(backend): add confidence quantification module
   fix(agent): handle timeout in tool execution
   docs(readme): update setup instructions
   ```

### Branch Naming

When creating branches:

1. **Use descriptive names:** `ticket-01-setup`, `feature/confidence-module`
2. **Use ticket prefixes:** Link tickets to branches (optional but recommended)
3. **Keep names concise:** Max 50 characters

### Pull Requests

When creating PRs:

1. **Link to tickets:** Reference affected ticket numbers
2. **Include screenshots:** If UI changes, show before/after
3. **Test cases:** List test cases that validate the change
4. **Breaking changes:** Clearly mark breaking changes with `BREAKING CHANGE:` prefix

---

## AI Agent-Specific Rules

### Subagent Dispatch

When dispatching a subagent:

1. **Use `delegate_task` with context:** Provide all relevant context in the `context` field
2. **Specify the toolset:** Include skills or tools the subagent needs (e.g., `["superpowers:to-tickets"]`)
3. **Set role as 'leaf':** The subagent works independently and reports back
4. **Expect to review:** Always review the subagent's output before marking complete

**Example:**
```typescript
delegate_task(
  goal="Break down the auto-osint design into actionable tickets",
  context="The auto-osint design document is at docs/superpowers/specs/2026-11-12-auto-osint-design.md",
  toolsets=["superpowers:to-tickets"],
  role="leaf"
)
```

### Agent Handoffs

When handing off work to another agent:

1. **Use the `handoff` skill:**
   ```typescript
   skill_view("handoff", "Continue implementing Ticket 01 - Setup Project Structure")
   ```

2. **Include summary:** What's been done, what's next
3. **Mention relevant artifacts:** Links to design docs, tickets, skills
4. **Suggest skills for next agent:** Which skills to use next

### Agent Review

When reviewing agent work:

1. **Read the ticket acceptance criteria:** What was promised vs. what was delivered
2. **Check the code:** Is it correct and follows conventions?
3. **Verify tests:** Do tests pass?
4. **Ask clarifying questions:** If anything is unclear, ask before approving

---

## Safety and Ethics

### Code Review Checklist

Before committing sensitive code:

1. **API keys:** Remove or obfuscate before committing
2. **Credentials:** Don't commit secrets to git
3. **PII:** Don't commit personally identifiable information
4. **Legal warnings:** Include appropriate disclaimers in documentation
5. **ToS compliance:** Ensure code respects platform Terms of Service

### Responsible Use

When implementing OSINT functionality:

1. **Respect ToS:** Don't bypass rate limits or anti-bot protections
2. **Legal compliance:** Ensure investigations are authorized and legal
3. **Privacy:** Don't target private individuals without authorization
4. **Document usage:** Include disclaimers about responsible use

---

## Tools and Utilities

### Common Commands

**Backend (Python):**
```bash
# Run development server
uv run uvicorn src.python.main:app --reload

# Run tests
uv run pytest

# Run linter
uv run ruff check src/
```

**Frontend (Next.js):**
```bash
# Run development server
npm run dev

# Build for production
npm run build

# Run tests
npm run test

# Run linter
npm run lint
```

### File Cleanup

When cleaning up:

1. **Don't delete tickets:** They are part of the plan
2. **Don't delete design docs:** They are reference material
3. **Delete scratch files:** `.scratch/*/` directory is safe to clean
4. **Remove old branches:** Delete merged and abandoned branches

---

## Getting Help

### When You're Stuck

1. **Check the skills:** Use `skill_view` to load relevant skills
2. **Read the AGENTS.md file:** You might have missed a rule
3. **Ask a human:** When unsure, ask for clarification
4. **Search the codebase:** Use `search_files` to find relevant code
5. **Check the design document:** Architecture decisions are documented there

### When You Need Context

1. **Ask the human:** "What's the current status of Ticket 01?"
2. **Read the ticket:** `/scratch/auto-osint/issues/01-*.md`
3. **Check git log:** See what was changed in recent commits
4. **Review recent files:** Look at recently created files

---

**Last Updated:** 2026-11-12  
**Maintained by:** AI agents working on auto-osint  
**Status:** Active
