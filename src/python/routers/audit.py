"""
Self-audit API.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..audit import run_audit
from ..database import get_db
from ..models.investigation import Investigation

router = APIRouter()


@router.get("/{investigation_id}")
def get_audit(investigation_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Run the audit for an investigation and return the report."""
    if db.get(Investigation, investigation_id) is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    return run_audit(db, investigation_id)
