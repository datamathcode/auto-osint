# 01: Setup Project Structure

**What to build:** A complete project structure with Next.js frontend, Python backend, TypeScript configuration, build tooling, and development environment. The agent and tools can run in local development mode.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

| - [x] Next.js or Vite project initialized with TypeScript
| - [x] Python backend (FastAPI) with async tool execution
| - [x] TypeScript configuration with strict mode
| - [x] npm/uv for package management
| - [x] Build scripts configured for frontend (npm run dev:frontend) and backend (uv run dev:backend)
| - [x] Environment variable configuration (.env.example and .env template)
| - [x] Git initialized with README and LICENSE
| - [x] PostgreSQL database schema created (SQLite initially for local development)

**Technical notes:**
- Use Next.js with App Router for React frontend
- Use uv (uvicorn) for Python backend
- Separate frontend and backend directories or monorepo with separate runtimes
- Include Git LFS for large assets if needed

**Implementation notes:**
- Project structure: Monorepo with frontend in `app/` and backend in `src/python/`
- Database: SQLite by default (`data/auto_osint.db`), PostgreSQL support configured
- Tech stack: Next.js 14, React 18, TypeScript 5, Tailwind CSS 3, FastAPI, SQLAlchemy
- Setup script: `src/python/scripts/setup_database.py` for database initialization
