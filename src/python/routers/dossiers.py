"""
Dossier API endpoints.

A dossier is the compiled read model for one investigation: the summary,
every evidence row, and every raw tool result.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.evidence import Evidence
from ..models.investigation import Investigation
from ..models.openosint_result import OpenOSINTResult

router = APIRouter()


def _evidence_to_dict(row: Evidence) -> Dict[str, Any]:
    return {
        "id": row.id,
        "source": row.source,
        "claim": row.claim,
        "confidence": row.confidence,
        "independence_score": row.independence_score,
        "corroborating_sources": row.corroborating_sources or [],
        "contradictions": row.contradictions or [],
        "links": row.links or [],
        "chain_of_custody": row.chain_of_custody or [],
    }


@router.get("/{investigation_id}")
def get_dossier(investigation_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Compile the dossier for one investigation."""
    investigation = db.get(Investigation, investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

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
        },
        "summary": {
            "evidence_count": len(evidence),
            "result_count": len(results),
            "mean_confidence": round(mean_confidence, 4),
            "high_confidence_count": sum(1 for c in confidences if c >= 0.7),
            "low_confidence_count": sum(1 for c in confidences if c < 0.4),
        },
        "evidence": [_evidence_to_dict(row) for row in evidence],
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
