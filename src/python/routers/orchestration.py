"""
Investigation orchestration endpoint.

Runs the plan/execute/observe/refine loop for one investigation, stores the
resulting evidence, and updates the investigation summary.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.investigation import Investigation
from ..orchestrator import Orchestrator
from ..tools.clients import SearchBreachClient, SearchEmailClient, SearchUsernameClient

router = APIRouter()


def build_tools() -> Dict[str, Any]:
    """Build the default tool set. Tests override this with stubs."""
    return {
        "search_username": SearchUsernameClient(),
        "search_email": SearchEmailClient(),
        "search_breach": SearchBreachClient(),
    }


class OrchestrateRequest(BaseModel):
    """Request body for running an investigation."""

    investigation_id: int
    claim: Optional[str] = None
    target: Optional[str] = None
    max_iterations: int = 2


@router.post("")
def orchestrate(payload: OrchestrateRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Run the orchestration loop and return the plan, report, and reasoning.

    Claim and target default to the investigation's own values. Tool failures
    are reported as gaps in the response rather than raising.
    """
    investigation = db.get(Investigation, payload.investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    claim = payload.claim or investigation.claim_under_investigation
    target = payload.target or investigation.target_id or investigation.target_name

    orchestrator = Orchestrator(
        tools=build_tools(),
        session=db,
        investigation_id=investigation.id,
        max_iterations=max(1, payload.max_iterations),
    )
    result = orchestrator.run(claim, target)

    investigation.net_confidence_score = result["reasoning"]["confidence"]
    stages = list(investigation.stages_completed or [])
    executed = [step["tool"] for step in result["plan"]["steps"]]
    investigation.stages_completed = sorted(set(stages + executed))
    if result["report"].get("summary", {}).get("failed", 0) == 0:
        investigation.status = "completed"

    db.commit()
    return result
