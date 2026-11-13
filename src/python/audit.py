"""
Self-auditing: gap detection, evidence weight, and source bias.

All heuristics are qualitative and rule-based; nothing here fabricates a
confidence number that the evidence does not support.
"""

import logging
from collections import Counter
from typing import Any, Dict, List, Optional

from .models.evidence import Evidence
from .models.investigation import Investigation
from .models.openosint_result import OpenOSINTResult

logger = logging.getLogger(__name__)

LOW_CONFIDENCE_THRESHOLD = 0.4
BIAS_SHARE_THRESHOLD = 0.7

QUESTION_TEMPLATES = {
    "funding": [
        "Who funds the target?",
        "Are there conflicts of interest between funder and target?",
        "Is the funding documented in a primary filing?",
    ],
    "intellectual_property": [
        "Who owns the intellectual property?",
        "Is the filing still active?",
        "Which jurisdictions cover the claim?",
    ],
    "social_presence": [
        "Which platforms does the target use?",
        "Are the accounts verified as belonging to the target?",
    ],
    "general": [
        "What primary document would settle the claim?",
        "Who benefits if the claim is believed?",
    ],
}

EXPECTED_SOURCE_TYPES = {
    "funding": ("sec", "filing", "registry", "tax", "bankruptcy"),
    "intellectual_property": ("uspto", "wipo", "espa", "patent", "trademark"),
    "social_presence": ("sherlock", "holehe", "social", "platform"),
    "general": ("primary", "official"),
}

EXPECTED_TOOLS = {
    "funding": ("search_breach",),
    "intellectual_property": (),
    "social_presence": ("search_username",),
    "general": ("search_username", "search_email"),
}

QUESTION_KEYWORDS = {
    "who funds the target?": ("fund", "invest", "donor", "backer"),
    "are there conflicts of interest between funder and target?": ("conflict", "interest", "overlap"),
    "is the funding documented in a primary filing?": ("filing", "sec", "registry"),
    "who owns the intellectual property?": ("patent", "trademark", "owns", "assignee"),
    "is the filing still active?": ("active", "expired", "status", "renew"),
    "which jurisdictions cover the claim?": ("jurisdiction", "uspto", "wipo", "euipo"),
    "which platforms does the target use?": ("platform", "account", "profile", "site"),
    "are the accounts verified as belonging to the target?": ("verified", "confirmed", "official"),
    "what primary document would settle the claim?": ("document", "filing", "record", "primary"),
    "who benefits if the claim is believed?": ("benefit", "interest", "fund"),
}


def claim_type_of(claim: str) -> str:
    from .orchestrator import classify_claim

    return classify_claim(claim)


def compile_questions(claim: str, claim_type: Optional[str] = None) -> List[str]:
    """Questions the claim raises, from templates keyed by claim type."""
    claim_type = claim_type or claim_type_of(claim)
    questions = list(QUESTION_TEMPLATES.get(claim_type, QUESTION_TEMPLATES["general"]))
    questions.insert(0, f"What evidence supports: {claim.strip()}?")
    return questions


def _evidence_text(evidence: List[Evidence]) -> str:
    return " ".join((row.claim or "").lower() for row in evidence)


def check_questions(questions: List[str], evidence: List[Evidence]) -> List[Dict[str, Any]]:
    """Mark each question answered when a keyword appears in stored evidence."""
    text = _evidence_text(evidence)
    results = []
    for question in questions:
        keywords = QUESTION_KEYWORDS.get(question.lower(), ())
        matched = [keyword for keyword in keywords if keyword in text]
        results.append(
            {
                "question": question,
                "answered": bool(matched),
                "matched_keywords": matched,
            }
        )
    return results


def missing_source_types(claim_type: str, evidence: List[Evidence], links: List[str]) -> List[str]:
    """Source categories the claim type expects but the evidence lacks."""
    expected = EXPECTED_SOURCE_TYPES.get(claim_type, EXPECTED_SOURCE_TYPES["general"])
    haystack = " ".join(
        [(row.source or "").lower() for row in evidence] + [link.lower() for link in links]
    )
    return [source for source in expected if source not in haystack]


def unqueried_tools(claim_type: str, results: List[OpenOSINTResult]) -> List[str]:
    """Tools that the claim type expects but which never ran."""
    ran = {result.tool for result in results}
    return [tool for tool in EXPECTED_TOOLS.get(claim_type, ()) if tool not in ran]


def weight_analysis(evidence: List[Evidence]) -> Dict[str, Any]:
    """Net confidence plus corroboration/contradiction counts."""
    confidences = [row.confidence for row in evidence if row.confidence is not None]
    net = sum(confidences) / len(confidences) if confidences else 0.0

    corroborated = sum(len(row.corroborating_sources or []) for row in evidence)
    contradictory = sum(len(row.contradictions or []) for row in evidence)

    return {
        "net_confidence": round(net, 4),
        "evidence_count": len(evidence),
        "corroborating_links": corroborated,
        "contradicting_links": contradictory,
        "low_confidence": net < LOW_CONFIDENCE_THRESHOLD,
        "single_source": len({row.source for row in evidence}) == 1 if evidence else False,
    }


def bias_analysis(evidence: List[Evidence]) -> Dict[str, Any]:
    """Source distribution and over-weighting flags."""
    counts = Counter(row.source for row in evidence if row.source)
    total = sum(counts.values())
    shares = {source: round(count / total, 3) for source, count in counts.items()} if total else {}

    dominated = [
        source for source, share in shares.items() if share >= BIAS_SHARE_THRESHOLD and total > 1
    ]

    primary_markers = ("sec", "filing", "registry", "uspto", "wipo", "official")
    primary = sum(
        1 for row in evidence if any(marker in (row.source or "").lower() for marker in primary_markers)
    )
    secondary = len(evidence) - primary

    return {
        "source_counts": dict(counts),
        "source_shares": shares,
        "dominated_by": dominated,
        "primary_sources": primary,
        "secondary_sources": secondary,
        "secondary_heavy": secondary > primary,
    }


def critical_gaps(
    claim_type: str,
    evidence: List[Evidence],
    weight: Dict[str, Any],
    missing_sources: List[str],
    unanswered: List[str],
) -> List[str]:
    """Gaps that undermine the conclusion rather than merely note absence."""
    gaps: List[str] = []

    if not evidence:
        gaps.append("No evidence was collected; the claim is unsupported.")
    elif weight["low_confidence"]:
        gaps.append(
            f"Net confidence {weight['net_confidence']:.2f} is below "
            f"{LOW_CONFIDENCE_THRESHOLD}; conclusions are weak."
        )

    if weight["single_source"] and weight["evidence_count"] > 1:
        gaps.append("All evidence comes from one source; independence is unproven.")

    if missing_sources:
        gaps.append(f"No {claim_type.replace('_', ' ')} primary sources found "
                    f"(missing: {', '.join(missing_sources)}).")

    if unanswered:
        gaps.append(f"{len(unanswered)} question(s) raised by the claim remain unanswered.")

    return gaps


def run_audit(session: Any, investigation_id: int) -> Dict[str, Any]:
    """Run the full audit and persist a compact report on the investigation."""
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
        .all()
    )

    claim_type = claim_type_of(investigation.claim_under_investigation or "")
    questions = compile_questions(investigation.claim_under_investigation or "", claim_type)
    checked = check_questions(questions, evidence)
    unanswered = [item["question"] for item in checked if not item["answered"]]

    links = [link for row in evidence for link in (row.links or [])]
    missing_sources = missing_source_types(claim_type, evidence, links)
    weight = weight_analysis(evidence)
    bias = bias_analysis(evidence)

    gaps = critical_gaps(claim_type, evidence, weight, missing_sources, unanswered)
    if unqueried_tools(claim_type, results):
        gaps.append(
            "Tools not queried for this claim type: "
            + ", ".join(unqueried_tools(claim_type, results))
        )

    report = {
        "investigation_id": investigation_id,
        "claim_type": claim_type,
        "questions": checked,
        "unanswered_questions": unanswered,
        "missing_source_types": missing_sources,
        "unqueried_tools": unqueried_tools(claim_type, results),
        "weight": weight,
        "bias": bias,
        "gaps": gaps,
        "critical_gap_count": len(gaps),
    }

    investigation.audit_report = report
    session.commit()

    return report
