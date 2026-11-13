"""
OpenOSINT results API.

Lists stored tool results by target, investigation, or tool name.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.investigation import Investigation
from ..models.openosint_result import OpenOSINTResult

router = APIRouter()


def _row_to_dict(row: OpenOSINTResult, investigation: Optional[Investigation]) -> Dict[str, Any]:
    return {
        "id": row.id,
        "investigation_id": row.investigation_id,
        "target_id": investigation.target_id if investigation else None,
        "target_name": investigation.target_name if investigation else None,
        "tool": row.tool,
        "target": row.target,
        "result": row.result,
        "source": row.source,
        "error": row.error,
        "timestamp": row.timestamp.isoformat() if row.timestamp else None,
    }


@router.get("")
def list_results(
    target_id: Optional[str] = Query(
        default=None, description="Investigation target_id or target_name"
    ),
    investigation_id: Optional[int] = Query(default=None),
    tool: Optional[str] = Query(default=None, description="Exact tool name"),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """List OpenOSINT results, newest first."""
    query = db.query(OpenOSINTResult, Investigation).join(
        Investigation, OpenOSINTResult.investigation_id == Investigation.id
    )

    if investigation_id is not None:
        query = query.filter(OpenOSINTResult.investigation_id == investigation_id)

    if target_id is not None:
        query = query.filter(
            (Investigation.target_id == target_id)
            | (Investigation.target_name == target_id)
        )

    if tool is not None:
        query = query.filter(OpenOSINTResult.tool == tool)

    rows = query.order_by(OpenOSINTResult.id.desc()).limit(limit).all()
    return [_row_to_dict(result, investigation) for result, investigation in rows]


@router.get("/{result_id}")
def get_result(result_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Fetch one stored tool result."""
    row = db.get(OpenOSINTResult, result_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Result not found")

    investigation = db.get(Investigation, row.investigation_id)
    return _row_to_dict(row, investigation)
