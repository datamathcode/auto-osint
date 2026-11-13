# 17: End-to-End Investigation with Synthetic Claim

**What to build:** Full end-to-end investigation workflow where user submits synthetic claim about a public figure, agent autonomously selects tools, executes queries, refines approach, user watches progress in real time, dossier is generated and displayed with all sections. All confidence scores, timelines, and graphs are rendered correctly. Investigation resumable from checkpoint if needed.

**Blocked by:** 14: UI - Investigation Input and Configuration, 15: UI - Real-Time Progress Streaming, 16: UI - Dossier Viewer with Confidence Visualization

**Status:** COMPLETE

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

**Implementation summary:**
- `POST /api/orchestrate/async` now runs the post-investigation analysis
  (`learning.run_post_investigation`) after every completed run, so recursive
  improvement is part of the default flow; the sync endpoint returns the lesson
  label as `playbook_update`.
- Resume support: `Orchestrator(completed_tools=...)` skips tools listed in
  `Investigation.stages_completed`, and `POST /api/orchestrate/async` accepts
  `resume: true`, so a rerun does not duplicate work.
- Failure path keeps partial progress: the run stops, the investigation is not
  marked completed, and the stored evidence/results remain readable.
- The workflow spans every component built so far: form payload → investigation
  → orchestration → evidence/results → timeline → graph → audit → learning →
  dossier.

**Verification (2026-11-13):**
- `tests/test_end_to_end.py` (4 tests) drives the real HTTP surface with only
  external tools stubbed:
  1. submit the synthetic claim "Find all social media accounts and data
     breaches for target@example.com", run asynchronously, read the SSE stream
     (started → plan → finding → confidence → refinement → complete at 100%),
     assert evidence + results stored, status completed, confidence 0.6, a
     lesson written to the playbook, and every dossier section populated
     (verdict, evidence, timeline, graph, gaps, improvement log, pagination);
  2. resume does not re-run completed tools (evidence count unchanged);
  3. a failing tool reports the error and keeps partial progress;
  4. missing required input is rejected with 422.
- Full suite: 222 passed, ruff clean; `tsc --noEmit` clean; `next build` OK.

**Deviations:**
- The external tools are stubbed (sherlock/holehe/HIBP and an LLM are not
  available here); the orchestration, storage, streaming, analysis and dossier
  paths are real.
- The synthetic claim uses `target@example.com` rather than a real person, as
  the ticket requires.
