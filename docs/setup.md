# Setup Guide

Quick start guide for setting up auto-osint locally.

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm
- PostgreSQL 14+ (optional - defaults to SQLite for local development)
- git

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/datamathcode/auto-osint.git
cd auto-osint
```

### 2. Install Dependencies

```bash
# Frontend dependencies
npm install

# Backend dependencies
cd src/python
uv pip install -r requirements.txt
cd ../..
```

### 3. Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your API keys and configuration:

- **LLM Provider:** `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or `OLLAMA_BASE_URL`
- **OpenOSINT Tools:** `HOLEHE_API_KEY`, `SHODAN_API_KEY`, etc.
- **Database:** `DATABASE_URL` (or leave default for SQLite)
- **Rate Limiting:** Configure per-tool limits
- **Execution Time:** Set `MAX_EXECUTION_TIME` and `TIMEOUT_PER_TOOL`

### 4. Initialize Database

```bash
# Using SQLite (default)
uv run python src/python/scripts/setup_database.py

# Using PostgreSQL
# Update DATABASE_URL in .env, then run:
uv run python src/python/scripts/setup_database.py
```

### 5. Verify Setup

Run the development servers:

```bash
# Terminal 1: Frontend
npm run dev:frontend

# Terminal 2: Backend
npm run dev:backend
```

Visit:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/health

## Configuration

### LLM Provider

**Anthropic (default):**
```bash
ANTHROPIC_API_KEY=sk-ant-...
```

**OpenAI:**
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-...
```

**Local Ollama:**
```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_API_KEY=ollama
```

### OpenOSINT Tools

Install and configure OSINT tools:

1. **SynINT:** Follow installation guide (https://github.com/gs-ai/SYNINT)
2. **OpenOSINT tools:** Install binaries and configure API keys
3. **Tools in PATH:** Ensure binaries are in your system PATH

### Database

**SQLite (default):**
- Database file: `data/auto_osint.db`
- No configuration needed

**PostgreSQL:**
- Install PostgreSQL
- Create database: `CREATE DATABASE auto_osint;`
- Set `DATABASE_URL=postgresql://user:pass@localhost:5432/auto_osint`

## Troubleshooting

### Dependencies Not Found

```bash
# Frontend
npm install

# Backend
cd src/python
uv pip install -r requirements.txt
```

### Database Errors

```bash
# Recreate database
rm data/auto_osint.db
uv run python src/python/scripts/setup_database.py
```

### Port Already in Use

```bash
# Change backend port in .env
API_PORT=8001
```

## Next Steps

1. Read the [Design Document](../superpowers/specs/2026-11-12-auto-osint-design.md)
2. Review [Ticket 01](../scratch/auto-osint/issues/01-setup-project-structure.md)
3. Check out the [AGENTS.md](../AGENTS.md) for agent conventions
4. Start building with Ticket 02: Base Agent and Tool Framework
