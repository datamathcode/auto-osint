# auto-osint — Project Setup Complete

**Date:** 2026-11-12  
**Status:** ✅ Design complete, skills installed, tickets published, repo created

---

## What We Accomplished

### 1. Requirements Discovery ✅

- Understood user's goal: autonomous OSINT research agent for public figures
- Clarified investigative depth: investigative journalism rigor with data journalism patterns
- Identified key requirements: recursive self-improvement, confidence quantification, pattern detection, timeline/network visualization, self-auditing

### 2. Research ✅

Researched existing solutions:
- **SYNINT**: 46 default agents, staged execution, relationship/timeline analysis, forensic reporting
- **OpenOSINT**: 11 tools, AI REPL, web UI, MCP server, real tool execution
- **Karpathy's Autoresearch**: Self-modifying research loops, structured program.md
- **Academic paper**: Agentic OSINT taxonomy, hallucination-validation gap, need for human-AI co-pilot

### 3. Design ✅

Created comprehensive design document covering:
- Intent and goals
- Non-goals and anti-goals
- Constraints and architectural decisions
- Data structures (Evidence Entry, Investigation Summary, Research Playbook)
- Recursive self-improvement loop
- Data journalism patterns (Bayesian confidence, independence testing, pattern detection, visualization)
- OSINT integration strategy
- Dossier output structure
- Platform and tooling

**Design decisions validated** via grilling skill with user:
- Recursive improvement frequency: every investigation
- Confidence algorithm: Bayesian inference
- Independence test: 3 core questions + 5 supporting checks
- Persistence: PostgreSQL + filesystem hybrid
- Guardrails: pre-built safeguards (scope config, rate limiting, warnings)
- Visualization: React Flow + D3.js
- Execution: concurrent run-all, staged pipeline
- Graph RAG: recommended for playbook retrieval
- Expand-Contract pattern: confidence quantification migration

### 4. Skills Installation ✅

Installed from mattpocock/skills:
- **Engineering**:
  - to-tickets: Break down plans into actionable tickets with blocking edges
  - grill-with-docs: Relentless interview to sharpen design (calls grilling + domain-modeling)
  - domain-modeling: Design domain models and data structures
- **Productivity**:
  - grilling: Stress-test plans, decisions, and ideas
  - handoff: Compact conversation context for other agents
  - writing-for-agents: Write documents for AI consumption

### 5. Ticket Breakdown ✅

Created 18 vertical slices with blocking edges:
1. Setup Project Structure
2. Base Agent and Tool Framework
3. Expand - Confidence Quantification Module
4. Migrate - First Batch: Evidence Entry Storage
5. Contract - Remove Old Evidence Storage Logic
6. Expand - Research Playbook Storage
7. Integrate SYNINT Agents (Basic Set)
8. Integrate OpenOSINT Tools (API Clients)
9. Base LLM Orchestration Layer
10. Recursive Improvement Loop
11. Timeline Reconstruction and Visualization
12. Network Graph Construction and Visualization
13. Self-Auditing and Gap Detection
14. UI - Investigation Input and Configuration
15. UI - Real-Time Progress Streaming
16. UI - Dossier Viewer with Confidence Visualization
17. End-to-End Investigation with Synthetic Claim
18. Documentation and Deployment Configuration

### 6. GitHub Repository ✅

Created and pushed to:
- **Organization**: datamathcode
- **Repository**: https://github.com/datamathcode/auto-osint
- **Branch**: main
- **Visibility**: Public
- **Files committed**: 31 files, 2189 insertions

---

## Project Structure

```
auto-osint/
├── .scratch/auto-osint/
│   └── issues/               # 18 published tickets (01-18)
│   └── TICKETS-PUBLISHED.md  # Ticket summary
├── docs/
│   └── superpowers/specs/
│       ├── 2026-11-12-auto-osint-design.md    # Complete design document
│       └── builder-check-prompt.md            # Builder review template
├── skills/
│   ├── README.md                          # Skills documentation
│   ├── engineering/
│   │   ├── domain-modeling/SKILL.md
│   │   ├── grill-with-docs/SKILL.md
│   │   └── to-tickets/SKILL.md
│   └── productivity/
│       ├── grilling/SKILL.md
│       ├── handoff/SKILL.md
│       └── writing-for-agents/SKILL.md
├── DESIGN-CHANGES.md        # Design review feedback applied
├── INSTALLED-SKILLS.md      # Skills installation summary
└── README.md                # Project overview and quick start
```

---

## Key Features Implemented in Design

### Recursive Self-Improvement
- Agent analyzes investigation outcomes after completion
- Identifies gaps and successful patterns
- Updates research playbook (MDX format)
- Next investigation loads updated playbook and adapts

### Data Journalism Rigor
- **Bayesian confidence quantification**: P(H|E) = P(E|H) × P(H) / P(E)
- **Independence testing**: 3 core questions + 5 supporting checks (0.0–1.0 score)
- **Pattern detection**: Temporal, network, geographic, financial patterns
- **Visualization**: D3.js for timelines, React Flow for networks
- **Self-auditing**: Gap detection, evidence weight analysis, bias detection

### OSINT Integration
- SYNINT agents for structured staged collection (46 default)
- OpenOSINT tools for cross-platform OSINT (11 core tools)
- Pluggable architecture following SYNINT/OpenOSINT patterns
- Custom agents/tools for corporate registry, financial, academic data

### Verifiable Output
- Every finding links to specific sources with confidence scores
- Evidence stored with full provenance (chain-of-custody)
- Dossier includes: summary, evidence, counter-evidence, timeline, network graph, gaps, improvement log
- All findings are human-readable and verifiable

---

## Technical Stack

- **Frontend**: Next.js + React + TypeScript + Tailwind CSS + D3.js + React Flow
- **Backend**: FastAPI + Python + LangChain + asyncio
- **Database**: PostgreSQL (structured data) + local filesystem (artifacts)
- **OSINT Integration**: SYNINT (agents) + OpenOSINT (tools)
- **LLM Providers**: Anthropic, OpenAI, Ollama
- **Deployment**: Vercel (recommended) or local Docker container

---

## Questions to Consider During Development

### Granularity
- If a ticket becomes too large, split it further
- Use vertical slicing to ensure each ticket is complete and demoable

### Blocking Edges
- Confirm tickets genuinely depend on each other
- Adjust dependencies if implementation reveals different relationships

### Scope
- Adapt tickets based on learnings during implementation
- Add more SYNINT/OpenOSINT tools if investigation needs require it
- Refine visualization complexity based on user feedback

### Graph RAG
- Consider implementing Graph RAG for playbook retrieval once the playbook grows beyond ~100 entries
- For initial implementation, keyword/semantic search may be sufficient

### Expand-Contract Pattern
- This pattern is critical for migrating confidence quantification and other deep integration changes
- Use it for any architectural changes that have blast radius across the codebase

---

## Next Steps

### Immediate Actions

1. **Clone and review the repository**:
   ```bash
   git clone https://github.com/datamathcode/auto-osint.git
   cd auto-osint
   ```

2. **Start with Ticket 01**: Setup Project Structure
   - Initialize Next.js + Python backend
   - Configure TypeScript, build tooling, development environment

3. **Follow dependency order**: Implement tickets sequentially, starting with unblocked tickets

4. **Use installed skills**:
   - `skill_view("grilling")`: Stress-test your decisions
   - `skill_view("grill-with-docs")`: Validate design as you go
   - `skill_view("to-tickets")`: Break down larger tickets if needed

### Recommended Workflow

1. **Read ticket**: Understand what needs to be built
2. **Implement**: Build the ticket following acceptance criteria
3. **Test**: Verify the ticket is complete and demoable on its own
4. **Validate**: Use grilling to stress-test your implementation
5. **Move on**: Proceed to next ticket with unblocked dependencies

### Alpha Build Iteration

- **Phase 1 (Collection)**: Tickets 01-08 (setup, framework, integrations)
- **Phase 2 (Reasoning)**: Tickets 09-10 (orchestration, recursive improvement)
- **Phase 3 (Analysis)**: Tickets 11-13 (timeline, graphs, self-auditing)
- **Phase 4 (UI)**: Tickets 14-16 (input, streaming, dossier viewer)
- **Phase 5 (Integration)**: Ticket 17 (end-to-end test)
- **Phase 6 (Polish)**: Ticket 18 (documentation and deployment)

---

## Repository Links

- **GitHub**: https://github.com/datamathcode/auto-osint
- **Design Document**: `/docs/superpowers/specs/2026-11-12-auto-osint-design.md`
- **Tickets**: `/scratch/auto-osint/issues/` (files 01-18)
- **Skills**: `/skills/` (grilling, handoff, writing-for-agents, to-tickets, grill-with-docs, domain-modeling)

---

## Design Validation Summary

All architectural decisions validated through grilling:

✅ Recursive improvement frequency: every investigation  
✅ Confidence algorithm: Bayesian inference  
✅ Independence testing: 3 core + 5 supporting checks  
✅ Persistence: PostgreSQL + filesystem hybrid  
✅ Guardrails: pre-built safeguards (scope, rate limiting, warnings)  
✅ Visualization: React Flow + D3.js  
✅ Execution: concurrent run-all, staged pipeline  
✅ Graph RAG: recommended for playbook retrieval  
✅ Expand-Contract pattern: critical for migrations  

---

**Project setup is complete. Development can begin immediately.**

Start with Ticket 01: Setup Project Structure.
