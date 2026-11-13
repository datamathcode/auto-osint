# Python Backend

FastAPI backend for auto-osint.

## Setup

```bash
# Install dependencies
uv pip install -r requirements.txt

# Set up database
uv run python scripts/setup_database.py
```

## Running

```bash
# Development server
uv run uvicorn src.python.main:app --reload

# Production server
uv run uvicorn src.python.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

- `GET /health` - Health check
- `GET /api/investigations` - List investigations
- `POST /api/investigations` - Create new investigation
- `GET /api/dossiers/{id}` - Get dossier by ID
- `WS /ws/investigations/{id}` - WebSocket for real-time progress

## Database

SQLite by default (`auto_osint.db`). Schema is defined in `models/`.
