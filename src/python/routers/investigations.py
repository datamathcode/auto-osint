"""
Investigation API endpoints.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.evidence import Evidence
from ..models.investigation import Investigation

router = APIRouter()


class InvestigationCreate(BaseModel):
    """Request body for creating an investigation."""

    target_name: str = Field(..., min_length=1)
    claim_under_investigation: str = Field(..., min_length=1)
    target_id: Optional[str] = None


class InvestigationUpdate(BaseModel):
    """Request body for updating an investigation."""

    status: Optional[str] = None
    investigation_notes: Optional[str] = None
    net_confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class InvestigationOut(BaseModel):
    """Serialized investigation."""

    id: int
    target_name: str
    target_id: Optional[str]
    claim_under_investigation: str
    status: str
    net_confidence_score: Optional[float]
    investigation_notes: Optional[str]

    model_config = {"from_attributes": True}


@router.post("", response_model=InvestigationOut, status_code=201)
def create_investigation(
    payload: InvestigationCreate, db: Session = Depends(get_db)
) -> Investigation:
    """Create an investigation in progress."""
    investigation = Investigation(
        target_name=payload.target_name,
        target_id=payload.target_id,
        claim_under_investigation=payload.claim_under_investigation,
        status="in_progress",
    )
    db.add(investigation)
    db.commit()
    db.refresh(investigation)
    return investigation


@router.get("", response_model=List[InvestigationOut])
def list_investigations(
    status: Optional[str] = None, db: Session = Depends(get_db)
) -> List[Investigation]:
    """List investigations, optionally filtered by status."""
    query = db.query(Investigation)
    if status:
        query = query.filter(Investigation.status == status)
    return query.order_by(Investigation.id.desc()).all()


@router.get("/{investigation_id}", response_model=InvestigationOut)
def get_investigation(
    investigation_id: int, db: Session = Depends(get_db)
) -> Investigation:
    """Fetch one investigation."""
    investigation = db.get(Investigation, investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return investigation


@router.patch("/{investigation_id}", response_model=InvestigationOut)
def update_investigation(
    investigation_id: int,
    payload: InvestigationUpdate,
    db: Session = Depends(get_db),
) -> Investigation:
    """Update status, notes, or the net confidence score."""
    investigation = db.get(Investigation, investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(investigation, field, value)

    db.commit()
    db.refresh(investigation)
    return investigation


@router.get("/{investigation_id}/evidence")
def list_evidence(
    investigation_id: int, db: Session = Depends(get_db)
) -> List[dict]:
    """List evidence rows for an investigation."""
    if db.get(Investigation, investigation_id) is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    rows = (
        db.query(Evidence)
        .filter(Evidence.investigation_id == investigation_id)
        .order_by(Evidence.id)
        .all()
    )
    return [
        {
            "id": row.id,
            "source": row.source,
            "claim": row.claim,
            "confidence": row.confidence,
            "independence_score": row.independence_score,
            "links": row.links or [],
        }
        for row in rows
    ]
