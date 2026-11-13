# 17: End-to-End Investigation with Synthetic Claim

**What to build:** Full end-to-end investigation workflow where user submits synthetic claim about a public figure, agent autonomously selects tools, executes queries, refines approach, user watches progress in real time, dossier is generated and displayed with all sections. All confidence scores, timelines, and graphs are rendered correctly. Investigation resumable from checkpoint if needed.

**Blocked by:** 14: UI - Investigation Input and Configuration, 15: UI - Real-Time Progress Streaming, 16: UI - Dossier Viewer with Confidence Visualization

**Status:** ready-for-agent

- [ ] User submits synthetic claim from investigation input page
- [ ] Agent runs full investigation with default configuration:
  - Uses LLM provider configured in API keys
  - Executes tools from SYNINT and OpenOSINT integrations
  - Executes recursive improvement (post-investigation analysis)
- [ ] User watches progress in real time via WebSocket/SSE
- [ ] Dossier is generated with all sections:
  - Summary (verdict, confidence score)
  - Evidence table with confidence color-coded
  - Counter-evidence section
  - Timeline visualization
  - Network graph visualization
  - Investigation gaps section
  - Recursive improvement log
- [ ] All confidence scores are accurate and source-verified
- [ ] Timeline shows all events with correct sources and confidence
- [ ] Network graph shows entities and relationships
- [ ] Gap detection identifies any missing sources
- [ ] Dossier can be viewed, exported as PDF
- [ ] Investigation is resumable from checkpoint (optional enhancement)
- [ ] Synthetic claim example: "Find all social media accounts and data breaches for target@example.com"

**Technical notes:**
- This is the end-to-end integration test
- Use synthetic data, not real public figure to avoid privacy/legal issues
- Verify all components work together: input → agent orchestration → evidence storage → analysis → visualization
- Performance: investigation completes within configured time window (default 5–60 min)
- Error handling: if investigation fails midway, report error and saved progress
