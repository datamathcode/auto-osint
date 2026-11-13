"""
Post-investigation learning loop.

After an investigation finishes, analyse what it produced, derive gaps and
successful patterns, and append a dated ``lessons_learned_<timestamp>`` section
to the research playbook. The next investigation loads the playbook and uses
those lessons when ordering tools.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import research_playbook
from .models.evidence import Evidence
from .models.investigation import Investigation
from .models.openosint_result import OpenOSINTResult

logger = logging.getLogger(__name__)

MAX_LESSONS_RETAINED = 10
LESSONS_KEY = "lessons_learned"


@dataclass
class InvestigationAnalysis:
    """Result of analysing one finished investigation."""

    investigation_id: int
    claim_type: str
    gaps: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    successful_tools: List[str] = field(default_factory=list)
    failed_tools: List[str] = field(default_factory=list)
    evidence_count: int = 0
    result_count: int = 0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "investigation_id": self.investigation_id,
            "claim_type": self.claim_type,
            "gaps": list(self.gaps),
            "patterns": list(self.patterns),
            "successful_tools": list(self.successful_tools),
            "failed_tools": list(self.failed_tools),
            "evidence_count": self.evidence_count,
            "result_count": self.result_count,
        }


def classify_claim_type(claim: str) -> str:
    """Reuse the orchestrator's classification without importing it lazily."""
    from .orchestrator import classify_claim

    return classify_claim(claim)


def analyze_investigation(session: Any, investigation_id: int) -> InvestigationAnalysis:
    """
    Read an investigation's stored evidence and tool results and score it.

    Gaps come from failed tool results and from claim types that produced no
    evidence. Patterns come from the tools that actually produced evidence.
    """
    investigation = session.get(Investigation, investigation_id)
    if investigation is None:
        raise ValueError(f"Investigation {investigation_id} not found")

    evidence = (
        session.query(Evidence)
        .filter(Evidence.investigation_id == investigation_id)
        .order_by(Evidence.id)
        .all()
    )
    results = (
        session.query(OpenOSINTResult)
        .filter(OpenOSINTResult.investigation_id == investigation_id)
        .order_by(OpenOSINTResult.id)
        .all()
    )

    analysis = InvestigationAnalysis(
        investigation_id=investigation_id,
        claim_type=classify_claim_type(investigation.claim_under_investigation or ""),
        evidence_count=len(evidence),
        result_count=len(results),
    )

    for result in results:
        if result.error:
            analysis.failed_tools.append(result.tool)
            analysis.gaps.append(f"{result.tool} failed: {result.error}")
        else:
            analysis.successful_tools.append(result.tool)

    if not evidence:
        analysis.gaps.append("no evidence was stored for this investigation")
    if not results:
        analysis.gaps.append("no tool results were stored for this investigation")

    sources = sorted({row.source for row in evidence})
    if sources:
        analysis.patterns.append(f"productive sources: {', '.join(sources)}")

    if analysis.successful_tools:
        ordered = list(dict.fromkeys(analysis.successful_tools))
        analysis.patterns.append(f"successful tool order: {', '.join(ordered)}")

    if evidence and not analysis.successful_tools:
        analysis.patterns.append("evidence came from agent runs, not registered tools")

    return analysis


def build_lesson(analysis: InvestigationAnalysis, label: Optional[str] = None) -> Dict[str, Any]:
    """Build one lesson record for the playbook."""
    stamp = label or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "label": f"{LESSONS_KEY}_{stamp}",
        "claim_type": analysis.claim_type,
        "recorded_at": stamp,
        "gaps": list(analysis.gaps),
        "patterns": list(analysis.patterns),
        "successful_tools": list(dict.fromkeys(analysis.successful_tools)),
        "evidence_count": analysis.evidence_count,
    }


def update_playbook(
    analysis: InvestigationAnalysis,
    path=None,
    label: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Append one lesson to the playbook, keeping the most recent lessons only.

    Incremental by design: existing sections and lessons are preserved, and the
    whole document is not rewritten from defaults.
    """
    previous_path = research_playbook.RESEARCH_PLAYBOOK_PATH
    if path is not None:
        research_playbook.RESEARCH_PLAYBOOK_PATH = path
    try:
        metadata = research_playbook.load() or {}
        lessons = list(metadata.get(LESSONS_KEY) or [])
        lesson = build_lesson(analysis, label=label)
        lessons.append(lesson)
        metadata[LESSONS_KEY] = lessons[-MAX_LESSONS_RETAINED:]
        research_playbook.save(metadata)
    finally:
        research_playbook.RESEARCH_PLAYBOOK_PATH = previous_path

    return lesson


def record_on_investigation(
    session: Any, investigation_id: int, lesson: Dict[str, Any]
) -> None:
    """Store the lesson reference on the investigation row."""
    investigation = session.get(Investigation, investigation_id)
    if investigation is None:
        raise ValueError(f"Investigation {investigation_id} not found")
    investigation.playbook_update = lesson["label"]
    session.commit()


def lessons_for_claim_type(metadata: Dict[str, Any], claim_type: str) -> List[Dict[str, Any]]:
    """Most recent first, filtered to a claim type."""
    lessons = metadata.get(LESSONS_KEY) or []
    matching = [item for item in lessons if item.get("claim_type") == claim_type]
    return list(reversed(matching))


def recommended_tools(metadata: Dict[str, Any], claim_type: str) -> List[str]:
    """
    Tools that previously succeeded for this claim type, most recent first.

    The orchestrator uses this to prioritise tools on the next investigation.
    """
    tools: List[str] = []
    for lesson in lessons_for_claim_type(metadata, claim_type):
        for tool in lesson.get("successful_tools") or []:
            if tool not in tools:
                tools.append(tool)
    return tools


def run_post_investigation(
    session: Any, investigation_id: int, path=None
) -> Dict[str, Any]:
    """Analyse, update the playbook, and record the reference."""
    analysis = analyze_investigation(session, investigation_id)
    lesson = update_playbook(analysis, path=path)
    record_on_investigation(session, investigation_id, lesson)

    return {
        "analysis": analysis.as_dict(),
        "lesson": lesson,
        "playbook_update": lesson["label"],
    }
