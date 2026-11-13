"""
FastAPI backend for auto-osint.
Provides API endpoints for investigations, dossiers, and OSINT tools.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .routers import investigations, dossiers

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

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "auto-osint backend is running"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
