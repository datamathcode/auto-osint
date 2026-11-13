"""
Investigation orchestration endpoint.

Runs the plan/execute/observe/refine loop for one investigation, stores the
resulting evidence, and updates the investigation summary.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import SessionLocal, get_db
from ..events import sink_for
from ..learning import run_post_investigation
from ..models.investigation import Investigation
from ..orchestrator import Orchestrator
from ..tools.clients import SearchBreachClient, SearchEmailClient, SearchUsernameClient

logger = logging.getLogger(__name__)

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
    resume: bool = False


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
        event_sink=sink_for(investigation.id),
        completed_tools=investigation.stages_completed if payload.resume else None,
    )
    result = orchestrator.run(claim, target)

    investigation.net_confidence_score = result["reasoning"]["confidence"]
    stages = list(investigation.stages_completed or [])
    executed = [step["tool"] for step in result["plan"]["steps"]]
    investigation.stages_completed = sorted(set(stages + executed))
    if result["report"].get("summary", {}).get("failed", 0) == 0:
        investigation.status = "completed"

    db.commit()

    # Recursive improvement: analyse the run and append a playbook lesson.
    try:
        result["playbook_update"] = run_post_investigation(db, investigation.id)["playbook_update"]
    except Exception as exc:
        logger.warning(f"post-investigation analysis failed: {exc}")
        result["playbook_update"] = None

    return result


def _run_background(investigation_id: int, claim: str, target: str, max_iterations: int) -> None:
    """Run one investigation on its own session, publishing progress events."""
    session = SessionLocal()
    try:
        investigation = session.get(Investigation, investigation_id)
        if investigation is None:
            logger.error(f"investigation {investigation_id} disappeared before the run")
            return

        orchestrator = Orchestrator(
            tools=build_tools(),
            session=session,
            investigation_id=investigation_id,
            max_iterations=max(1, max_iterations),
            event_sink=sink_for(investigation_id),
            completed_tools=investigation.stages_completed,
        )
        try:
            result = orchestrator.run(claim, target)
        except Exception as exc:  # report, never leave subscribers hanging
            logger.exception("background investigation failed")
            sink_for(investigation_id)(
                {
                    "type": "investigation_complete",
                    "message": f"Investigation failed: {exc}",
                    "data": {"error": str(exc)},
                    "progress": 100,
                }
            )
            investigation.status = "failed"
            session.commit()
            return

        investigation.net_confidence_score = result["reasoning"]["confidence"]
        stages = list(investigation.stages_completed or [])
        investigation.stages_completed = sorted(
            set(stages + [step["tool"] for step in result["plan"]["steps"]])
        )
        if result["report"].get("summary", {}).get("failed", 0) == 0:
            investigation.status = "completed"
        session.commit()

        try:
            run_post_investigation(session, investigation_id)
        except Exception as exc:
            logger.warning(f"post-investigation analysis failed: {exc}")
    finally:
        session.close()


@router.post("/async", status_code=202)
async def orchestrate_async(
    payload: OrchestrateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Start an investigation in the background and stream progress separately."""
    investigation = db.get(Investigation, payload.investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    claim = payload.claim or investigation.claim_under_investigation
    target = payload.target or investigation.target_id or investigation.target_name

    investigation.status = "in_progress"
    db.commit()

    background_tasks.add_task(
        _run_background,
        investigation.id,
        claim,
        target,
        max(1, payload.max_iterations),
    )

    return {
        "investigation_id": investigation.id,
        "status": "started",
        "sse_url": f"/sse/investigation/{investigation.id}",
        "ws_url": f"/ws/investigation/{investigation.id}",
    }
