# 15: UI - Real-Time Progress Streaming

**What to build:** WebSocket or Server-Sent Events streaming of investigation progress. Per-step output: tool execution, findings, confidence updates. User can see agent's reasoning and decision-making in real time. Progress indicator (percentage complete, current stage).

**Blocked by:** 09: Base LLM Orchestration Layer

**Status:** COMPLETE

- [ ] Backend WebSocket endpoint `/ws/investigation/<id>` for real-time streaming
- [ ] Backend SSE endpoint `/sse/investigation/<id>` (alternative to WebSocket)
- [ ] Progress steps include:
  - Investigation started
  - Plan generation
  - Tool execution (tool name, target, status)
  - Findings (what was discovered)
  - Confidence updates
  - Plan refinement
  - Investigation complete
- [ ] Per-step output formatting:
  - Tool execution: tool name, target, status, elapsed time
  - Findings: claim, source, confidence score
  - Confidence updates: new confidence, reasoning
- [ ] Frontend WebSocket client:
  - Connects to backend endpoint
  - Displays progress updates in real time
  - Shows current stage (e.g., "Executing WhoisAgent", "Analyzing results")
  - Progress percentage calculation (based on total steps)
  - Error messages on tool failures
  - Auto-reconnect on connection drop
- [ ] UI elements:
  - Progress bar
  - Status log with timestamps
  - Step cards for each progress update
- [ ] End-to-end test: start investigation, verify real-time updates, check progress indicator

**Technical notes:**
- Use Python `asyncio` and `websockets` or FastAPI SSE
- Progress calculation is heuristic based on expected number of steps
- Messages are JSON: `{type, step, message, data, timestamp}`
- Streaming stops when investigation completes or fails
- Progress persists across page refreshes (optional enhancement)

**Implementation summary:**
- `src/python/events.py`: thread-safe `EventBus` with per-investigation
  subscribers, 50-event replay for late subscribers, 200-event history, and
  drop-on-full delivery so a slow consumer cannot block a run.
- `Orchestrator` gained `event_sink` and emits: `investigation_started` (5%),
  `plan_generated` (10%), `step_started`, `finding`, `step_finished`,
  `confidence_updated`, `refinement` (95%), `investigation_complete` (100%).
  A failing sink never breaks the run.
- `src/python/routers/streaming.py`
  - `GET /sse/investigation/{id}` — SSE with keep-alive comments, 404 for
    unknown ids, ends on the terminal event.
  - `WS /ws/investigation/{id}` — same stream over WebSocket with heartbeats.
- `POST /api/orchestrate/async` (202) — starts the run in a background task on
  its own session and returns the SSE/WS URLs.
- `app/investigations/[id]/progress/page.tsx` — WebSocket client with
  exponential-backoff reconnect (6 attempts), progress bar, timestamped status
  log, step cards, and failure highlighting; the investigate form now routes
  here when "run immediately" is checked.

**Verification (2026-11-13):**
- `tests/test_streaming.py` (12 tests): bus delivery/replay/unsubscribe/overflow,
  full orchestrator event sequence with progress bounds (5→100), sink failure
  isolation, 202 + completion, SSE payload parsing, 404 for unknown id, and
  WebSocket delivery ending on the terminal event.
- Full suite: 209 passed, ruff clean.
- `tsc --noEmit` clean; `next build` emits `/investigations/[id]/progress`.
