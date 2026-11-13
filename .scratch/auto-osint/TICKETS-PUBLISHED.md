# auto-osint Tickets Published

**Date:** 2026-11-12  
**Repository:** https://github.com/datamathcode/auto-osint  
**Status:** All 18 tickets published and pushed to GitHub

---

## Tickets Published

All tickets are located in `.scratch/auto-osint/issues/` and tagged with `ready-for-agent`.

### Sequential Dependencies

1. **Ticket 01**: Setup Project Structure (no blockers)
2. **Ticket 02**: Base Agent and Tool Framework (blocks: 01)
3. **Ticket 03**: Expand - Confidence Quantification Module (blocks: 02)
4. **Ticket 04**: Migrate - First Batch: Evidence Entry Storage (blocks: 03)
5. **Ticket 05**: Contract - Remove Old Evidence Storage Logic (blocks: 04)
6. **Ticket 06**: Expand - Research Playbook Storage (blocks: 05)
7. **Ticket 07**: Integrate SYNINT Agents (Basic Set) (blocks: 06)
8. **Ticket 08**: Integrate OpenOSINT Tools (API Clients) (blocks: 07)
9. **Ticket 09**: Base LLM Orchestration Layer (blocks: 07-08)
10. **Ticket 10**: Recursive Improvement Loop (blocks: 09)
11. **Ticket 11**: Timeline Reconstruction and Visualization (blocks: 09-10)
12. **Ticket 12**: Network Graph Construction and Visualization (blocks: 09-10)
13. **Ticket 13**: Self-Auditing and Gap Detection (blocks: 09-10)
14. **Ticket 14**: UI - Investigation Input and Configuration (blocks: 07-08)
15. **Ticket 15**: UI - Real-Time Progress Streaming (blocks: 09)
16. **Ticket 16**: UI - Dossier Viewer with Confidence Visualization (blocks: 11-12-13)
17. **Ticket 17**: End-to-End Investigation with Synthetic Claim (blocks: 14-15-16)
18. **Ticket 18**: Documentation and Deployment Configuration (blocks: 17)

---

## Horizontal Dependencies

- Tickets 11-13 are mutually dependent (timeline, graphs, self-auditing)
- Tickets 07-08 are independent of each other but block Ticket 09
- Tickets 14-15-16 are UI tickets that depend on backend completion

---

## Key Design Patterns Applied

1. **Expand-Contract Pattern**:
   - Tickets 03-04-05: Confidence quantification
   - Pattern keeps each batch manageable and preserves existing functionality

2. **Vertical Slicing**:
   - Each ticket cuts a complete path through layers (schema, API, UI, tests)
   - Each ticket is complete and demoable on its own

3. **Recursive Improvement**:
   - Ticket 10 establishes the feedback loop that improves future investigations
   - Learning is incremental and playbook-based

---

## Project Structure

```
auto-osint/
├── .scratch/auto-osint/issues/
│   ├── 01-setup-project-structure.md
│   ├── 02-base-agent-framework.md
│   ├── 03-expand-confidence-module.md
│   ├── 04-migrate-first-batch-evidence.md
│   ├── 05-contract-old-evidence-storage.md
│   ├── 06-expand-research-playbook-storage.md
│   ├── 07-integrate-synint-agents.md
│   ├── 08-integrate-openosint-tools.md
│   ├── 09-base-llm-orchestration-layer.md
│   ├── 10-recursive-improvement-loop.md
│   ├── 11-timeline-reconstruction-visualization.md
│   ├── 12-network-graph-construction-visualization.md
│   ├── 13-self-auditing-gap-detection.md
│   ├── 14-ui-investigation-input-config.md
│   ├── 15-ui-real-time-progress-streaming.md
│   ├── 16-ui-dossier-viewer.md
│   ├── 17-end-to-end-investigation-synthetic-claim.md
│   └── 18-documentation-deployment-config.md
├── docs/
│   └── superpowers/specs/
│       ├── 2026-11-12-auto-osint-design.md
│       └── builder-check-prompt.md
├── skills/
│   ├── README.md
│   ├── engineering/
│   │   ├── domain-modeling/SKILL.md
│   │   ├── grill-with-docs/SKILL.md
│   │   └── to-tickets/SKILL.md
│   └── productivity/
│       ├── grilling/SKILL.md
│       ├── handoff/SKILL.md
│       └── writing-for-agents/SKILL.md
├── DESIGN-CHANGES.md
├── INSTALLED-SKILLS.md
└── README.md
```

---

## Repository URL

**GitHub:** https://github.com/datamathcode/auto-osint

The repo is public and ready for development to begin. All design decisions have been validated, skills are installed, and tickets are published.

---

## Next Steps

1. **Start with Ticket 01**: Setup Project Structure
   - Initialize Next.js + Python backend
   - Configure TypeScript, build tooling, development environment

2. **Follow blocking edges**: Implement tickets in dependency order

3. **Use installed skills**:
   - `grilling`: Stress-test implementation as you go
   - `grill-with-docs`: Validate architecture and design
   - `to-tickets`: Break down larger tickets if needed

4. **Iterate with alpha builds**: Focus on one layer at a time (collection → reasoning → UI)

5. **End-to-end testing**: Ticket 17 validates the complete system

---

## Questions to Consider During Development

- **Granularity adjustments**: If a ticket becomes too large, split it further
- **Blocking edge verification**: Confirm tickets genuinely depend on each other
- **Scope changes**: Adapt tickets based on learnings during implementation
- **Tool selection**: May need to add more SYNINT/OpenOSINT tools based on investigation needs
- **Visualization complexity**: Timeline and graph visualizations may need iteration

---

**Development can begin at Ticket 01. All prerequisites and dependencies are defined.**
