# 15: UI - Real-Time Progress Streaming

**What to build:** WebSocket or Server-Sent Events streaming of investigation progress. Per-step output: tool execution, findings, confidence updates. User can see agent's reasoning and decision-making in real time. Progress indicator (percentage complete, current stage).

**Blocked by:** 09: Base LLM Orchestration Layer

**Status:** ready-for-agent

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
