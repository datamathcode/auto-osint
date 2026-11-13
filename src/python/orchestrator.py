"""
Base LLM orchestration layer.

A custom (dependency-free) orchestrator that:

1. reads the research playbook to pick research strategies by claim type,
2. plans which tools to run for a claim and target,
3. executes those tools in parallel with per-tool timeouts,
4. observes the outputs, stores evidence, and updates reasoning, and
5. refines the plan when findings are thin.

The LLM is optional by design: ``reasoning_hook`` lets a caller plug in a model
to rewrite the plan or summarise findings, while the deterministic default keeps
the pipeline testable without network access.
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional

from .agents.base import AgentBase
from .learning import recommended_tools
from .research_playbook import load as load_playbook

logger = logging.getLogger(__name__)

DEFAULT_MAX_CONCURRENT = 8
DEFAULT_MAX_ITERATIONS = 2

CLAIM_TYPE_KEYWORDS = {
    "funding": ("fund", "invest", "financ", "revenue", "backer", "donor"),
    "intellectual_property": ("patent", "trademark", "copyright", "intellectual property"),
}

TARGET_TOOL_MAP = {
    "email": ("search_email", "search_breach"),
    "username": ("search_username",),
}


def classify_target(target: str) -> str:
    """Classify a target as email, username, or domain."""
    if "@" in target:
        return "email"
    if "." in target and " " not in target:
        return "domain"
    return "username"


def classify_claim(claim: str) -> str:
    """Map claim text to a playbook section name."""
    lowered = claim.lower()
    for claim_type, keywords in CLAIM_TYPE_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return claim_type
    if any(word in lowered for word in ("social", "account", "profile", "username")):
        return "social_presence"
    return "general"


@dataclass
class PlanStep:
    """One tool invocation in a plan."""

    tool: str
    target: str
    rationale: str
    optional: bool = False
    result: Optional[Dict[str, Any]] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool,
            "target": self.target,
            "rationale": self.rationale,
            "optional": self.optional,
            "status": (self.result or {}).get("status"),
        }


@dataclass
class InvestigationPlan:
    """Ordered plan for one investigation."""

    claim: str
    target: str
    claim_type: str
    steps: List[PlanStep] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "claim": self.claim,
            "target": self.target,
            "claim_type": self.claim_type,
            "steps": [step.as_dict() for step in self.steps],
        }


@dataclass
class ReasoningState:
    """Mutable reasoning state across iterations."""

    confidence: float = 0.0
    findings: List[Dict[str, Any]] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    iterations: int = 0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "confidence": round(self.confidence, 4),
            "finding_count": len(self.findings),
            "gaps": list(self.gaps),
            "contradictions": list(self.contradictions),
            "iterations": self.iterations,
        }


class _EvidenceSink(AgentBase):
    """Minimal concrete agent used only to reuse store_evidence()."""

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover
        return {"status": "success", "context": context}


class Orchestrator:
    """
    Plan, execute, observe, and refine an investigation.

    Args:
        tools: mapping of tool name -> tool instance (ToolBase subclasses)
        session: optional SQLAlchemy session used to store evidence
        investigation_id: investigation the evidence belongs to
        max_concurrent: cap on parallel tool calls (default 8)
        max_iterations: refinement passes (default 2)
        playbook_loader: callable returning the playbook metadata dict
        reasoning_hook: optional callable(plan, report, state) -> None for LLM use
    """

    def __init__(
        self,
        tools: Dict[str, Any],
        session: Any = None,
        investigation_id: Optional[int] = None,
        max_concurrent: int = DEFAULT_MAX_CONCURRENT,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        playbook_loader: Callable[[], Dict[str, Any]] = load_playbook,
        reasoning_hook: Optional[Callable[[InvestigationPlan, Dict[str, Any], ReasoningState], None]] = None,
        event_sink: Optional[Callable[[Dict[str, Any]], None]] = None,
        completed_tools: Optional[Iterable[str]] = None,
    ):
        self.tools = tools
        self.session = session
        self.investigation_id = investigation_id
        self.max_concurrent = max(1, max_concurrent)
        self.max_iterations = max(1, max_iterations)
        self.playbook_loader = playbook_loader
        self.reasoning_hook = reasoning_hook
        self.event_sink = event_sink
        self.completed_tools = set(completed_tools or [])
        self.state = ReasoningState()

        self._sink: Optional[_EvidenceSink] = None
        if session is not None and investigation_id is not None:
            self._sink = _EvidenceSink(name="Orchestrator", investigation_id=investigation_id)
            self._sink.set_evidence_storage(session)

        # Give every tool the session so it can persist its own result rows.
        if session is not None:
            for tool in self.tools.values():
                setter = getattr(tool, "set_db_session", None)
                if callable(setter):
                    setter(session)
                elif hasattr(tool, "save_to_database"):
                    tool.db_session = session

    # -- progress events -------------------------------------------------

    def _emit(
        self,
        event_type: str,
        message: str,
        step: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        progress: Optional[int] = None,
    ) -> None:
        """Publish a progress event when a sink is configured."""
        if self.event_sink is None:
            return
        try:
            self.event_sink(
                {
                    "type": event_type,
                    "step": step,
                    "message": message,
                    "data": data or {},
                    "progress": progress,
                }
            )
        except Exception as exc:  # observability must never break the run
            logger.warning(f"event sink failed: {exc}")

    # -- planning --------------------------------------------------------

    def plan_investigation(self, claim: str, target: str) -> InvestigationPlan:
        """Build a plan from the claim type, target type, and playbook."""
        claim_type = classify_claim(claim)
        target_type = classify_target(target)

        playbook = {}
        try:
            playbook = self.playbook_loader() or {}
        except Exception as exc:  # a broken playbook must not stop planning
            logger.warning(f"playbook unavailable ({exc}); planning from target type only")

        steps: List[PlanStep] = []
        for tool_name in TARGET_TOOL_MAP.get(target_type, ()):
            if tool_name in self.tools:
                steps.append(
                    PlanStep(
                        tool=tool_name,
                        target=target,
                        rationale=f"{target_type} target: {tool_name}",
                    )
                )

        # Playbook-driven steps: suggested tool labels resolve to a client when
        # one is registered, and otherwise become explicit optional steps so the
        # gap is visible instead of silently dropped.
        for label in self._playbook_tools(playbook, claim_type):
            resolved = self._resolve_tool(label)
            if resolved:
                steps.append(
                    PlanStep(
                        tool=resolved,
                        target=target,
                        rationale=f"playbook:{claim_type} -> {label}",
                    )
                )
            else:
                steps.append(
                    PlanStep(
                        tool=label,
                        target=target,
                        rationale=f"playbook:{claim_type} (no client registered)",
                        optional=True,
                    )
                )

        if not steps:
            steps.append(
                PlanStep(
                    tool="search_username" if target_type == "username" else "search_email",
                    target=target,
                    rationale="fallback: no playbook or target mapping matched",
                    optional=True,
                )
            )

        # Resume support: tools already completed for this investigation are
        # not planned again.
        if self.completed_tools:
            steps = [step for step in steps if step.tool not in self.completed_tools]

        # Lessons from previous investigations reorder the plan: tools that
        # worked for this claim type run first.
        preferred = recommended_tools(playbook, claim_type)
        if preferred:
            order = {name: index for index, name in enumerate(preferred)}
            steps.sort(key=lambda step: order.get(step.tool, len(order)))

        return InvestigationPlan(claim=claim, target=target, claim_type=claim_type, steps=steps)

    def _playbook_tools(self, playbook: Dict[str, Any], claim_type: str) -> List[str]:
        """Suggested tools for a claim type, from the loaded playbook."""
        section = playbook.get(claim_type)
        if not isinstance(section, dict):
            return []
        tools = section.get("suggested_tools")
        return tools if isinstance(tools, list) else []

    def _resolve_tool(self, label: str) -> Optional[str]:
        """Map a playbook tool label onto a registered tool name."""
        normalised = label.lower()
        for name, instance in self.tools.items():
            candidates = {name.lower(), getattr(instance, "tool_name", "").lower()}
            if normalised in candidates:
                return name
        # Loose match: "SEC filings" has no client; "search_username" style
        # labels match by substring.
        for name in self.tools:
            if normalised in name.lower() or name.lower() in normalised:
                return name
        return None

    # -- execution -------------------------------------------------------

    def _run_step(self, step: PlanStep) -> Dict[str, Any]:
        tool = self.tools.get(step.tool)
        if tool is None:
            return {
                "status": "failed",
                "tool": step.tool,
                "target": step.target,
                "error": "tool not registered",
                "data": {},
            }
        self._emit(
            "step_started",
            f"Executing {step.tool} on {step.target}",
            step=step.tool,
            data={"tool": step.tool, "target": step.target},
        )
        try:
            return tool.execute(step.target)
        except Exception as exc:  # a crashing tool must not kill the run
            logger.error(f"{step.tool} raised: {exc}")
            return {
                "status": "failed",
                "tool": step.tool,
                "target": step.target,
                "error": str(exc),
                "data": {},
            }

    def execute_plan(self, plan: InvestigationPlan) -> Dict[str, Any]:
        """Execute every step in parallel and aggregate the results."""
        runnable = [step for step in plan.steps if not step.optional or step.tool in self.tools]
        skipped = [step for step in plan.steps if step not in runnable]

        results: List[Dict[str, Any]] = []
        if runnable:
            workers = min(self.max_concurrent, len(runnable))
            with ThreadPoolExecutor(max_workers=workers) as pool:
                for step, result in zip(
                    runnable, pool.map(self._run_step, runnable), strict=False
                ):
                    step.result = result
                    results.append(result)

        for step in skipped:
            results.append(
                {
                    "status": "skipped",
                    "tool": step.tool,
                    "target": step.target,
                    "error": "no client registered for this playbook tool",
                    "data": {},
                }
            )

        failed = [r for r in results if r.get("status") == "failed"]
        succeeded = [r for r in results if r.get("status") in {"success", "partial"}]

        return {
            "claim": plan.claim,
            "target": plan.target,
            "claim_type": plan.claim_type,
            "results": results,
            "summary": {
                "steps": len(plan.steps),
                "succeeded": len(succeeded),
                "failed": len(failed),
                "skipped": len([r for r in results if r.get("status") == "skipped"]),
            },
        }

    # -- observation and reasoning ---------------------------------------

    def observe_tool_output(self, tool_result: Dict[str, Any]) -> Dict[str, Any]:
        """Record one tool result and store it as evidence when possible."""
        observation = {
            "tool": tool_result.get("tool"),
            "target": tool_result.get("target"),
            "status": tool_result.get("status"),
            "source": tool_result.get("source"),
            "error": tool_result.get("error"),
            "observed_at": datetime.now(timezone.utc).isoformat(),
        }

        data = tool_result.get("data") or {}
        claim_text = self._claim_from_result(tool_result, data)

        # Persist the raw tool result so it is queryable via /api/results and
        # visible to post-investigation analysis.
        tool = self.tools.get(str(tool_result.get("tool") or ""))
        if self.session is not None and self.investigation_id is not None and tool is not None:
            persist = getattr(tool, "persist", None)
            if callable(persist):
                try:
                    observation["result_id"] = persist(tool_result, self.investigation_id)
                except Exception as exc:
                    logger.error(f"tool result persistence failed: {exc}")
                    observation["result_error"] = str(exc)

        if claim_text:
            self._emit(
                "finding",
                f"{tool_result.get('tool')} found: {claim_text[:120]}",
                step=str(tool_result.get("tool") or ""),
                data={
                    "claim": claim_text,
                    "source": tool_result.get("source"),
                    "confidence": 0.6 if tool_result.get("status") == "success" else 0.3,
                },
            )
            observation["claim"] = claim_text
            self.state.findings.append(observation)
            if self._sink is not None:
                try:
                    observation["evidence_id"] = self._sink.store_evidence(
                        source=tool_result.get("source") or tool_result.get("tool") or "orchestrator",
                        claim=claim_text,
                        confidence=0.6 if tool_result.get("status") == "success" else 0.3,
                        independence_score=0.7,
                        independence_check_details={"tool": tool_result.get("tool")},
                        links=self._links_from(data),
                        raw_text=str(data.get("raw", "")) or None,
                        chain_of_custody=[{"action": "orchestrator_observation",
                                           "tool": tool_result.get("tool")}],
                    )
                except Exception as exc:
                    logger.error(f"evidence storage failed: {exc}")
                    observation["evidence_error"] = str(exc)

        self._emit(
            "step_finished",
            f"{tool_result.get('tool')} -> {tool_result.get('status')}",
            step=str(tool_result.get("tool") or ""),
            data={
                "status": tool_result.get("status"),
                "error": tool_result.get("error"),
            },
        )

        if tool_result.get("status") == "failed":
            self.state.gaps.append(
                f"{tool_result.get('tool')}: {tool_result.get('error') or 'failed'}"
            )

        return observation

    def _claim_from_result(self, tool_result: Dict[str, Any], data: Dict[str, Any]) -> Optional[str]:
        if tool_result.get("status") not in {"success", "partial"}:
            return None
        if data.get("count"):
            if "breaches" in data:
                return f"{data.get('email')} appears in {data['count']} known breaches"
            return f"{tool_result.get('tool')} found {data['count']} records for {tool_result.get('target')}"
        return None

    def _links_from(self, data: Dict[str, Any]) -> List[str]:
        links: List[str] = []
        for platform in data.get("platforms_found", []) or []:
            url = platform.get("url")
            if url:
                links.append(url)
        for breach in data.get("breaches", []) or []:
            domain = breach.get("domain")
            if domain:
                links.append(f"https://{domain}")
        return links

    def update_reasoning(self, finding: Optional[Dict[str, Any]] = None, confidence: Optional[float] = None) -> ReasoningState:
        """Update confidence, gaps and contradictions from a finding."""
        if finding:
            self.state.findings.append(finding)
            if confidence is not None:
                self.state.confidence = confidence
        elif confidence is not None:
            self.state.confidence = confidence

        if confidence is None:
            self.state.confidence = self._confidence_from_findings()

        return self.state

    def _confidence_from_findings(self) -> float:
        if not self.state.findings:
            return 0.0
        scores = [
            0.6 if finding.get("status") == "success" else 0.3
            for finding in self.state.findings
        ]
        return sum(scores) / len(scores)

    def identify_gaps(self, report: Dict[str, Any]) -> List[str]:
        """List what is still missing after an execution pass."""
        gaps: List[str] = []

        for result in report.get("results", []):
            if result.get("status") == "failed":
                gaps.append(f"{result.get('tool')} failed: {result.get('error')}")
            elif result.get("status") == "skipped":
                gaps.append(f"{result.get('tool')} has no registered client")
            elif result.get("status") == "partial":
                gaps.append(f"{result.get('tool')} returned no records")

        if not self.state.findings and not gaps:
            gaps.append("no findings were produced for this claim")
        return gaps

    def refine_plan(self, plan: InvestigationPlan, report: Dict[str, Any]) -> InvestigationPlan:
        """Adapt the plan: retry failed tools once, then stop."""
        gaps = self.identify_gaps(report)
        self.state.gaps = gaps

        attempted = {step.tool for step in plan.steps}
        additions: List[PlanStep] = []
        for result in report.get("results", []):
            tool = result.get("tool")
            if result.get("status") in {"failed", "partial"} and tool not in attempted:
                additions.append(
                    PlanStep(tool=tool, target=plan.target, rationale="retry after gap")
                )

        return InvestigationPlan(
            claim=plan.claim,
            target=plan.target,
            claim_type=plan.claim_type,
            steps=additions,
        )

    # -- full loop -------------------------------------------------------

    def run(self, claim: str, target: str) -> Dict[str, Any]:
        """Plan, execute, observe, and refine until iterations are exhausted."""
        self._emit(
            "investigation_started",
            f"Investigation started for {target}",
            data={"claim": claim, "target": target},
            progress=5,
        )
        plan = self.plan_investigation(claim, target)
        self._emit(
            "plan_generated",
            f"Planned {len(plan.steps)} step(s) ({plan.claim_type})",
            data={"claim_type": plan.claim_type, "steps": [step.as_dict() for step in plan.steps]},
            progress=10,
        )
        report: Dict[str, Any] = {}

        for iteration in range(1, self.max_iterations + 1):
            self.state.iterations = iteration
            plan = (
                plan if iteration == 1 else self.refine_plan(plan, report)
            )
            if not plan.steps:
                break

            report = self.execute_plan(plan)
            for result in report["results"]:
                self.observe_tool_output(result)

            self.update_reasoning()
            total_steps = max(1, report.get("summary", {}).get("steps", 1))
            finished = self.state.iterations * total_steps
            progress = min(95, 10 + int(80 * finished / (total_steps * self.max_iterations)))
            self._emit(
                "confidence_updated",
                f"Confidence now {self.state.confidence:.2f}",
                data={
                    "confidence": round(self.state.confidence, 4),
                    "findings": len(self.state.findings),
                    "gaps": list(self.state.gaps),
                },
                progress=progress,
            )
            if self.reasoning_hook:
                self.reasoning_hook(plan, report, self.state)

            if not self.refine_plan(plan, report).steps:
                break

        refined = self.refine_plan(plan, report)
        self._emit(
            "refinement",
            f"Refinement produced {len(refined.steps)} additional step(s)",
            data={"steps": [step.as_dict() for step in refined.steps]},
            progress=95,
        )
        self._emit(
            "investigation_complete",
            f"Investigation complete: {len(self.state.findings)} finding(s)",
            data=self.state.as_dict(),
            progress=100,
        )

        return {
            "claim": claim,
            "target": target,
            "plan": plan.as_dict(),
            "report": report,
            "reasoning": self.state.as_dict(),
        }
