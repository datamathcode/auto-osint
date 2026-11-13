"""
Timeline API.

Returns the reconstructed timeline for one investigation, optionally refreshed
from the underlying evidence, and can persist it to ``timeline_events``.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.investigation import Investigation
from ..timeline import build_timeline, persist_timeline

router = APIRouter()


@router.get("/{investigation_id}")
def get_timeline(
    investigation_id: int,
    persist: bool = Query(default=False, description="Store the events in timeline_events"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Reconstruct the timeline for an investigation."""
    if db.get(Investigation, investigation_id) is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    timeline = build_timeline(db, investigation_id)

    if persist:
        timeline["persisted"] = persist_timeline(db, investigation_id, timeline)

    return timeline
