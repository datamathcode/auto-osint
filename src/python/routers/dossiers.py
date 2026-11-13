"""
Dossier API endpoints.

A dossier is the compiled read model for one investigation: verdict, evidence,
counter-evidence, timeline, graph, gaps, and the latest learning record.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import research_playbook
from ..audit import run_audit
from ..database import get_db
from ..graph import build_graph
from ..learning import lessons_for_claim_type
from ..models.evidence import Evidence
from ..models.investigation import Investigation
from ..models.openosint_result import OpenOSINTResult
from ..timeline import build_timeline

router = APIRouter()


def verdict_for(confidence: float) -> str:
    """Map net confidence to a plain-language verdict."""
    if confidence >= 0.7:
        return "supported"
    if confidence >= 0.4:
        return "inconclusive"
    return "unsupported"


def _evidence_to_dict(row: Evidence) -> Dict[str, Any]:
    return {
        "id": row.id,
        "source": row.source,
        "claim": row.claim,
        "confidence": row.confidence,
        "independence_score": row.independence_score,
        "independence_check_details": row.independence_check_details,
        "corroborating_sources": row.corroborating_sources or [],
        "contradictions": row.contradictions or [],
        "links": row.links or [],
        "chain_of_custody": row.chain_of_custody or [],
        "raw_text": row.raw_text,
    }


def _investigation_or_404(db: Session, investigation_id: int) -> Investigation:
    investigation = db.get(Investigation, investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return investigation


@router.get("/{investigation_id}")
def get_dossier(investigation_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Compile the dossier for one investigation."""
    investigation = _investigation_or_404(db, investigation_id)

    evidence: List[Evidence] = (
        db.query(Evidence)
        .filter(Evidence.investigation_id == investigation_id)
        .order_by(Evidence.id)
        .all()
    )
    results: List[OpenOSINTResult] = (
        db.query(OpenOSINTResult)
        .filter(OpenOSINTResult.investigation_id == investigation_id)
        .order_by(OpenOSINTResult.id)
        .all()
    )

    confidences = [row.confidence for row in evidence if row.confidence is not None]
    mean_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    return {
        "investigation": {
            "id": investigation.id,
            "target_name": investigation.target_name,
            "target_id": investigation.target_id,
            "claim_under_investigation": investigation.claim_under_investigation,
            "status": investigation.status,
            "net_confidence_score": investigation.net_confidence_score,
            "investigation_notes": investigation.investigation_notes,
            "playbook_update": investigation.playbook_update,
        },
        "verdict": verdict_for(investigation.net_confidence_score or mean_confidence),
        "summary": {
            "evidence_count": len(evidence),
            "result_count": len(results),
            "mean_confidence": round(mean_confidence, 4),
            "high_confidence_count": sum(1 for c in confidences if c >= 0.7),
            "medium_confidence_count": sum(1 for c in confidences if 0.4 <= c < 0.7),
            "low_confidence_count": sum(1 for c in confidences if c < 0.4),
            "counter_evidence_count": len([row for row in evidence if row.contradictions]),
        },
        "evidence": [_evidence_to_dict(row) for row in evidence],
        "counter_evidence": [
            _evidence_to_dict(row) for row in evidence if row.contradictions
        ],
        "results": [
            {
                "id": row.id,
                "tool": row.tool,
                "target": row.target,
                "result": row.result,
                "source": row.source,
                "error": row.error,
            }
            for row in results
        ],
    }


@router.get("/{investigation_id}/evidence")
def get_dossier_evidence(
    investigation_id: int,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Paginated evidence table for the dossier viewer."""
    _investigation_or_404(db, investigation_id)

    query = db.query(Evidence).filter(Evidence.investigation_id == investigation_id)
    total = query.count()
    rows = query.order_by(Evidence.id).offset(offset).limit(limit).all()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": offset + len(rows) < total,
        "evidence": [_evidence_to_dict(row) for row in rows],
    }


@router.get("/{investigation_id}/timeline")
def get_dossier_timeline(investigation_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Timeline data for the dossier viewer."""
    _investigation_or_404(db, investigation_id)
    return build_timeline(db, investigation_id)


@router.get("/{investigation_id}/graph")
def get_dossier_graph(investigation_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Entity graph data for the dossier viewer."""
    _investigation_or_404(db, investigation_id)
    return build_graph(db, investigation_id)


@router.get("/{investigation_id}/gaps")
def get_dossier_gaps(investigation_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Gap-detection results for the dossier viewer."""
    _investigation_or_404(db, investigation_id)
    return run_audit(db, investigation_id)


@router.get("/{investigation_id}/playbook-update")
def get_dossier_playbook_update(
    investigation_id: int, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Latest learning record relevant to this investigation."""
    investigation = _investigation_or_404(db, investigation_id)

    metadata: Dict[str, Any] = {}
    try:
        metadata = research_playbook.load() or {}
    except Exception:
        metadata = {}

    from ..orchestrator import classify_claim

    claim_type = classify_claim(investigation.claim_under_investigation or "")
    lessons = lessons_for_claim_type(metadata, claim_type)

    return {
        "investigation_id": investigation_id,
        "claim_type": claim_type,
        "reference": investigation.playbook_update,
        "latest_lessons": lessons[:5],
    }
