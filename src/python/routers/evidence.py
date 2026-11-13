"""
Evidence query API.

Supports listing stored evidence by investigation, by target identifier
(the investigation's target_id or target_name), or by source.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.evidence import Evidence
from ..models.investigation import Investigation

router = APIRouter()


def _row_to_dict(row: Evidence, investigation: Optional[Investigation]) -> Dict[str, Any]:
    return {
        "id": row.id,
        "investigation_id": row.investigation_id,
        "target_id": investigation.target_id if investigation else None,
        "target_name": investigation.target_name if investigation else None,
        "source": row.source,
        "timestamp": row.timestamp.isoformat() if row.timestamp else None,
        "claim": row.claim,
        "confidence": row.confidence,
        "independence_score": row.independence_score,
        "links": row.links or [],
        "raw_text": row.raw_text,
    }


@router.get("")
def list_evidence(
    target_id: Optional[str] = Query(
        default=None, description="Investigation target_id or target_name"
    ),
    investigation_id: Optional[int] = Query(default=None),
    source: Optional[str] = Query(default=None, description="Exact source match"),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    List evidence rows.

    With no filters, returns the newest rows first. `target_id` matches an
    investigation's target_id or target_name so callers can ask "what evidence
    do we hold about example.com" without knowing internal IDs.
    """
    query = db.query(Evidence, Investigation).join(
        Investigation, Evidence.investigation_id == Investigation.id
    )

    if investigation_id is not None:
        query = query.filter(Evidence.investigation_id == investigation_id)

    if target_id is not None:
        query = query.filter(
            (Investigation.target_id == target_id)
            | (Investigation.target_name == target_id)
        )

    if source is not None:
        query = query.filter(Evidence.source == source)

    rows = query.order_by(Evidence.id.desc()).limit(limit).all()
    return [_row_to_dict(evidence, investigation) for evidence, investigation in rows]


@router.get("/{evidence_id}")
def get_evidence(evidence_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Fetch one evidence row with its full chain of custody."""
    row = db.get(Evidence, evidence_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Evidence not found")

    investigation = db.get(Investigation, row.investigation_id)
    body = _row_to_dict(row, investigation)
    body["chain_of_custody"] = row.chain_of_custody or []
    body["independence_check_details"] = row.independence_check_details
    body["corroborating_sources"] = row.corroborating_sources or []
    body["contradictions"] = row.contradictions or []
    return body
