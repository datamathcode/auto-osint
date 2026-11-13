# 09: Base LLM Orchestration Layer

**What to build:** LangChain or custom agent orchestrator that reads the research playbook, selects tools based on claim type and findings, executes tools with timeout enforcement, observes outputs, and updates reasoning. Agent can run simple investigation end-to-end (e.g., "Find all social accounts for johndoe").

**Blocked by:** 07: Integrate SYNINT Agents (Basic Set), 08: Integrate OpenOSINT Tools (API Clients)

**Status:** ready-for-agent

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
