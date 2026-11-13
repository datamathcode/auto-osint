"""
Entity graph API.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..graph import EDGE_COLORS, build_graph, filter_graph, persist_graph
from ..models.investigation import Investigation

router = APIRouter()


@router.get("/{investigation_id}")
def get_graph(
    investigation_id: int,
    edge_type: Optional[str] = Query(default=None, description="Filter to one edge type"),
    min_degree: int = Query(default=0, ge=0, description="Drop nodes below this degree"),
    persist: bool = Query(default=False, description="Store a graph snapshot"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Build the entity graph, optionally filtered and/or persisted."""
    if db.get(Investigation, investigation_id) is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    graph = build_graph(db, investigation_id)
    if edge_type or min_degree:
        graph = filter_graph(graph, edge_type=edge_type, min_degree=min_degree)

    if persist:
        graph["persisted"] = persist_graph(db, investigation_id, graph)

    graph["edge_colors"] = EDGE_COLORS
    return graph
