# 09: Base LLM Orchestration Layer

**What to build:** LangChain or custom agent orchestrator that reads the research playbook, selects tools based on claim type and findings, executes tools with timeout enforcement, observes outputs, and updates reasoning. Agent can run simple investigation end-to-end (e.g., "Find all social accounts for johndoe").

**Blocked by:** 07: Integrate SYNINT Agents (Basic Set), 08: Integrate OpenOSINT Tools (API Clients)

**Status:** COMPLETE

- [ ] Agent orchestrator class with:
  - `plan_investigation(claim, target)` method
  - `execute_plan(plan)` method
  - `observe_tool_output(tool_result)` method
  - `update_reasoning(finding, confidence)` method
- [ ] Playbook loading and parsing
- [ ] Tool selection logic:
  - Reads claim type from playbook
  - Selects suggested tools for that claim type
  - Adapts based on real-time findings
- [ ] Tool execution:
  - Parallel execution with timeout enforcement
  - Result aggregation and error handling
- [ ] Reasoning loop:
  - Updates internal reasoning state
  - Identifies gaps or contradictions
  - Refines plan for next iteration
- [ ] End-to-end test: investigate synthetic claim, run full pipeline, display results

**Technical notes:**
- Use LangChain for orchestration if available, otherwise custom implementation
- Agent should maintain conversation history of investigations
- Parallel execution: max 8 concurrent tool calls (configurable)
- Each tool gets its own timeout (60s default)
- Results are stored as evidence with source metadata

**Implementation summary:**
- `src/python/orchestrator.py`: custom, dependency-free orchestration
  (LangChain is not imported anywhere).
  - `plan_investigation(claim, target)` — classifies target (email / username /
    domain) and claim (funding / intellectual_property / social_presence /
    general), then builds steps from target mappings plus playbook
    `suggested_tools`. Unknown playbook labels become explicit optional steps so
    the gap is visible.
  - `execute_plan(plan)` — `ThreadPoolExecutor` with `max_concurrent` (default
    8); per-tool timeouts come from each tool; failures are captured, never
    raised.
  - `observe_tool_output(result)` — records findings, writes evidence through
    `AgentBase.store_evidence` (source, links, raw text, chain of custody), and
    turns failures into gaps.
  - `update_reasoning(finding, confidence)` — maintains findings, confidence,
    gaps, contradictions, iterations.
  - `refine_plan(plan, report)` and `run(claim, target)` — bounded refinement
    loop (default 2 iterations) that only re-runs tools that failed or came back
    partial, so work is not duplicated.
  - `reasoning_hook(plan, report, state)` lets an LLM rewrite or narrate the
    plan without coupling the pipeline to a provider.
- `POST /api/orchestrate` — runs the loop for an investigation, stores evidence,
  and updates `net_confidence_score`, `stages_completed`, and status.

**Verification (2026-11-13):**
- `tests/test_orchestrator.py` (20 tests): classification, planning with and
  without playbook, unregistered playbook tools, parallel timing (two 0.4s
  tools finish under 0.75s), failure isolation, gap detection, evidence
  persistence, loop bounds (single pass when nothing new to run), a real
  `SearchUsernameClient` driving the pipeline, HIBP missing-key gap, and the
  `/api/orchestrate` endpoint (including 404).
- Full suite: 130 passed, ruff clean.

**Deviation:** no LLM provider is wired in. The plan/observe/refine loop is
deterministic and model-agnostic; `reasoning_hook` is the integration point for
an LLM once a provider and key are configured.
