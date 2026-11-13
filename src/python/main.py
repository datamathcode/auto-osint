"""
FastAPI backend for auto-osint.
Provides API endpoints for investigations, dossiers, and OSINT tools.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import (
    audit,
    config,
    dossiers,
    evidence,
    graph,
    investigations,
    orchestration,
    results,
    timeline,
)

# Create FastAPI app
app = FastAPI(
    title="auto-osint API",
    description="Agentic recursive OSINT research API",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(investigations.router, prefix="/api/investigations", tags=["investigations"])
app.include_router(dossiers.router, prefix="/api/dossiers", tags=["dossiers"])
app.include_router(evidence.router, prefix="/api/evidence", tags=["evidence"])
app.include_router(results.router, prefix="/api/results", tags=["results"])
app.include_router(orchestration.router, prefix="/api/orchestrate", tags=["orchestration"])
app.include_router(timeline.router, prefix="/api/timeline", tags=["timeline"])
app.include_router(graph.router, prefix="/api/graph", tags=["graph"])
app.include_router(audit.router, prefix="/api/audit", tags=["audit"])
app.include_router(config.router, prefix="/api/config", tags=["config"])

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "auto-osint backend is running"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
