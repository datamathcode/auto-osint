"""
Timeline reconstruction.

Turns stored evidence, chain-of-custody entries, and tool results into a sorted
event list with roles, sources, confidence, and contradiction hints.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models.evidence import Evidence
from .models.investigation import Investigation
from .models.openosint_result import OpenOSINTResult
from .models.timeline_event import TimelineEvent

logger = logging.getLogger(__name__)

YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")
DATE_PATTERN = re.compile(r"\b((19|20)\d{2})-(\d{2})-(\d{2})\b")

ROLE_COLORS = {
    "statement": "#3b82f6",
    "publication": "#8b5cf6",
    "observation": "#10b981",
    "collection": "#f59e0b",
}


def _parse_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def extract_event_date(text: str) -> Optional[datetime]:
    """Return the first full date (YYYY-MM-DD) mentioned in text, if any."""
    match = DATE_PATTERN.search(text or "")
    if not match:
        return None
    try:
        return datetime(int(match.group(1)), int(match.group(3)), int(match.group(4)))
    except ValueError:
        return None


def extract_event_year(text: str) -> Optional[int]:
    match = YEAR_PATTERN.search(text or "")
    return int(match.group(0)) if match else None


def event_role(claim: str, action: Optional[str] = None) -> str:
    """Classify an event into one of the four roles."""
    if action:
        return "collection"
    lowered = (claim or "").lower()
    if any(word in lowered for word in ("published", "article", "press release", "filed", "report")):
        return "publication"
    return "statement"


def _event(
    role: str,
    title: str,
    timestamp: Optional[datetime],
    detail: str = "",
    source: Optional[str] = None,
    confidence: float = 0.0,
    links: Optional[List[str]] = None,
    evidence_id: Optional[int] = None,
    group_name: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "role": role,
        "title": title,
        "detail": detail,
        "timestamp": (timestamp or datetime.now(timezone.utc).replace(tzinfo=None)).isoformat(),
        "source": source,
        "confidence": round(float(confidence or 0.0), 4),
        "links": links or [],
        "evidence_id": evidence_id,
        "group": group_name or source or role,
        "color": ROLE_COLORS.get(role, "#6b7280"),
    }


def build_timeline(session: Any, investigation_id: int) -> Dict[str, Any]:
    """
    Build the timeline for one investigation.

    Ordering: explicit dates found in claims sort first (they describe the world),
    collection events use the evidence timestamp.
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

    events: List[Dict[str, Any]] = []

    for row in evidence:
        role = event_role(row.claim)
        dated = extract_event_date(row.claim)
        timestamp = dated or _parse_dt(row.timestamp)
        events.append(
            _event(
                role=role,
                title=row.claim,
                timestamp=timestamp,
                detail=f"Evidence #{row.id} from {row.source}",
                source=row.source,
                confidence=row.confidence or 0.0,
                links=row.links or [],
                evidence_id=row.id,
                group_name=row.source,
            )
        )

        for entry in row.chain_of_custody or []:
            if not isinstance(entry, dict):
                continue
            action = entry.get("action") or entry.get("discovery_type")
            if not action:
                continue
            events.append(
                _event(
                    role="collection",
                    title=f"Collected: {action}",
                    timestamp=_parse_dt(entry.get("timestamp")) or _parse_dt(row.timestamp),
                    detail=f"Evidence #{row.id}",
                    source=row.source,
                    confidence=row.confidence or 0.0,
                    evidence_id=row.id,
                    group_name=row.source,
                )
            )

    for row in results:
        events.append(
            _event(
                role="observation",
                title=f"{row.tool} observed {row.target}",
                timestamp=_parse_dt(row.timestamp),
                detail=(row.result or {}).get("summary") or str(row.result)[:200],
                source=row.source or row.tool,
                confidence=0.0 if row.error else 0.4,
                group_name=row.tool,
            )
        )

    events.sort(key=lambda event: event["timestamp"])

    return {
        "investigation_id": investigation_id,
        "target": investigation.target_name,
        "events": events,
        "roles": sorted({event["role"] for event in events}),
        "groups": sorted({event["group"] for event in events}),
        "contradictions": detect_temporal_contradictions(events),
        "date_range": {
            "start": events[0]["timestamp"] if events else None,
            "end": events[-1]["timestamp"] if events else None,
        },
    }


def detect_temporal_contradictions(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Flag events about the same subject that claim different years.

    The heuristic is deliberately simple: same source and a shared subject word,
    different years.
    """
    dated = []
    for event in events:
        if event["role"] not in {"statement", "publication"}:
            continue
        year = extract_event_year(event["title"])
        if year:
            dated.append((event, year))

    contradictions = []
    for index, (event_a, year_a) in enumerate(dated):
        for event_b, year_b in dated[index + 1:]:
            if year_a == year_b:
                continue
            words_a = {word for word in re.findall(r"[a-z]{4,}", event_a["title"].lower())}
            words_b = {word for word in re.findall(r"[a-z]{4,}", event_b["title"].lower())}
            if event_a["source"] == event_b["source"] and words_a & words_b:
                contradictions.append(
                    {
                        "subject": sorted(words_a & words_b)[0],
                        "years": [year_a, year_b],
                        "events": [event_a["title"], event_b["title"]],
                        "sources": [event_a["source"], event_b["source"]],
                    }
                )
    return contradictions


def persist_timeline(session: Any, investigation_id: int, timeline: Dict[str, Any]) -> int:
    """Replace the stored timeline rows for an investigation."""
    session.query(TimelineEvent).filter(
        TimelineEvent.investigation_id == investigation_id
    ).delete()

    count = 0
    for event in timeline["events"]:
        session.add(
            TimelineEvent(
                investigation_id=investigation_id,
                timestamp=_parse_dt(event["timestamp"]),
                role=event["role"],
                title=event["title"],
                detail=event["detail"],
                source=event["source"],
                confidence=event["confidence"],
                links=event["links"],
                evidence_id=event["evidence_id"],
                group_name=event["group"],
            )
        )
        count += 1
    session.commit()
    return count
