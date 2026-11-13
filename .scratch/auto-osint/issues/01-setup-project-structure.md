# 01: Setup Project Structure

**What to build:** A complete project structure with Next.js frontend, Python backend, TypeScript configuration, build tooling, and development environment. The agent and tools can run in local development mode.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Next.js or Vite project initialized with TypeScript
- [ ] Python backend (FastAPI or Flask) with async tool execution
- [ ] TypeScript configuration with strict mode
- [ ] npm/uv for package management
- [ ] Build scripts configured for frontend (npm run dev) and backend (uv run dev)
- [ ] Environment variable configuration (.env.example and .env template)
- [ ] Git initialized with README and LICENSE
- [ ] PostgreSQL database schema created (SQLite initially for local development)

**Technical notes:**
- Use Next.js with App Router for React frontend
- Use uv (uvicorn) for Python backend
- Separate frontend and backend directories or monorepo with separate runtimes
- Include Git LFS for large assets if needed
